"""Especialistas. Cada um recebe o Context e devolve AgentResult com status explícito:
"ok", "insufficient" (não tem base para responder) ou "error". O supervisor decide o que
fazer com cada status — nenhum agente chama outro.

Regra para rodar em paralelo: agente só LÊ o Context; o que descobre volta em `facts` e o
supervisor junta depois, na ordem do plano. Nada de escrever em ctx dentro do agente.

- faq: RAG (retriever de rag.get_retriever) com fonte citada; "sem fonte, sem afirmação". A consulta passa
  pelo glossário pt<->en (data/glossary.json) antes da busca. Intent "general": câmbio (PTAX) e clima (Open-Meteo)
  consultados no código (app/live_data.py, texto bruto da API como evidência); o resto, e qualquer falha da API,
  pela busca web, com os resultados da busca como evidência e fonte (nunca a própria resposta).
- records: tools com identidade do servidor; escrita só propõe (action_id + confirmação).
- escalation: abre caso na fila persistida; operador responde em /operator (ou Telegram) e a conversa retoma.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

from . import capabilities, domain, grounding, live_data, memory
from .actions import run_tool, tool_specs
from .config import coverage_gate, coverage_min_cosine, coverage_min_score, data_dir
from .llm import LLMError, get_llm
from .notify import notify_new_ticket
from .rag import get_retriever
from .schemas import Handoff, Source, ToolCall
from .store import get_store

# MIN_SCORE (portão sem fonte) e ELIGIBLE_STATUS são do DOMÍNIO; `agents.MIN_SCORE` segue valendo (__getattr__).
# Híbrido: trecho sem termo em comum (sinônimo) só conta como fonte com cosseno >= MIN_COSINE E perto do
# melhor cosseno da busca (COSINE_MARGIN). Medido no corpus de exemplo com o MiniLM multilíngue (30/10/2026):
# sinônimo certo 0,44; vizinhos de pergunta bem respondida 0,50–0,53 com o melhor em 0,75; pergunta sem
# fonte <= 0,19. O cosseno muda de escala com o modelo: recalibre no corpus real, com o eval.
MIN_COSINE = 0.4
COSINE_MARGIN = 0.15
MAX_TOOL_ROUNDS = 3
_PROMPTS = Path(__file__).parent / "prompts"
# Busca web do servidor da Anthropic (o modelo decide a consulta; a API executa e devolve com citação).
# Variante 20260209 (filtro dinâmico) vale para Opus 5.5/Sonnet 5.5; modelo antigo ou Vertex: web_search_20250305.
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 2}


@dataclass
class Context:
    text: str
    language: str
    user_id: str
    conversation_id: str
    intent: str = "faq"
    history: list[dict] = field(default_factory=list)
    user_summary: str = ""
    conversation_digest: str = ""  # falas desta conversa que saíram da janela recente (pipeline._digest)
    ledger: str = ""  # "Fatos da conversa": ids, valores e assunto extraídos por código (app/memory.py)
    facts: dict = field(default_factory=dict)
    handoff_reason: str | None = None


@dataclass
class AgentResult:
    agent: str
    status: str
    text: str = ""
    sources: list[Source] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    reason: str | None = None
    pending_action: str | None = None
    handoff: Handoff | None = None
    evidence: list[str] = field(default_factory=list)  # base dos números: fonte, resultado de tool, template
    # Achados que pedem outro especialista: [{"agent": "faq", "why": "...", "hint": "..."}]. O supervisor insere o
    # passo se a transição estiver em ALLOWED e houver orçamento (replanejamento por achado, não só por falha).
    needs: list[dict] = field(default_factory=list)

    def for_supervisor(self) -> str:
        """O que o supervisor LLM enxerga como tool_result: status, texto e fatos — nada de dado bruto extra."""
        return json.dumps({"status": self.status, "reason": self.reason, "text": self.text, "facts": self.facts,
                           "sources": [s.id for s in self.sources], "pending_action": self.pending_action,
                           "needs": self.needs},
                          ensure_ascii=False)


def _t(ctx: Context, pt: str, en: str) -> str:
    return en if ctx.language == "en" else pt


def llm_history(ctx: Context, final_user: str) -> list[dict]:
    """Memória curta: últimos 10 turnos + resumo de longo prazo, em mensagens alternadas user/assistant."""
    msgs: list[dict] = []
    for m in ctx.history[-10:]:
        role = "user" if m["role"] == "user" else "assistant"
        content = m["content"] if m["role"] != "human_agent" else f"[atendente humano] {m['content']}"
        if msgs and msgs[-1]["role"] == role:
            msgs[-1]["content"] += "\n" + content
        else:
            msgs.append({"role": role, "content": content})
    if msgs and msgs[0]["role"] == "assistant":
        msgs.pop(0)
    if ctx.conversation_digest:
        final_user = f"[antes nesta conversa] {ctx.conversation_digest}\n\n{final_user}"
    if ctx.ledger:
        final_user = f"{ctx.ledger}\n\n{final_user}"
    if ctx.user_summary:
        final_user = f"[memória do usuário] {ctx.user_summary}\n\n{final_user}"
    if msgs and msgs[-1]["role"] == "user":
        msgs[-1]["content"] += "\n" + final_user
    else:
        msgs.append({"role": "user", "content": final_user})
    return msgs


def latest_eligible(items: list[dict], tool: str, status_key: str = "status") -> dict | None:
    """O item mais recente (fim da lista) cujo status permite a ação; None = nenhum serve, não proponha nada."""
    allowed = domain.active().ELIGIBLE_STATUS.get(tool)
    fit = [i for i in items if allowed is None or i.get(status_key) in allowed]
    return fit[-1] if fit else None


def _today() -> str:
    d = date.today()  # data local do servidor; o prompt não pode adivinhar o dia ("tomorrow (Oct 30)" num dia 31)
    return f"{d.isoformat()} ({d.strftime('%A')})"


# --- glossário: busca entre idiomas -----------------------------------------------------------
def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


@lru_cache(maxsize=4)
def _glossary_for(path: str, mtime: float) -> tuple[tuple[str, tuple[str, ...]], ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple((pt, tuple(en)) for pt, en in raw.items() if not pt.startswith("_") and isinstance(en, list))


def glossary() -> tuple[tuple[str, tuple[str, ...]], ...]:
    path = data_dir() / "glossary.json"
    try:
        return _glossary_for(str(path), path.stat().st_mtime)  # recarrega se o arquivo mudar
    except FileNotFoundError:
        return ()


def _has(folded_text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(_fold(term))}(?!\w)", folded_text) is not None


def expand_query(text: str) -> str:
    """Acrescenta à consulta os termos do outro idioma (glossário pt<->en), por palavra ou expressão inteira.

    Getnet v3 (31/10/2026): "How many installments in Crediário?" não achava o documento em português; a mesma
    pergunta em português trazia o relevante em 1º. O texto original vem primeiro e fica intacto; termo que não
    existe no corpus não muda o score BM25 dos documentos. Mesma expansão com e sem LLM (a busca vem antes).
    """
    folded = _fold(text)
    extra: list[str] = []
    for pt, ens in glossary():
        if _has(folded, pt):
            extra += [e for e in ens if not _has(folded, e)]
        elif any(_has(folded, e) for e in ens):
            extra.append(pt)
    extra = list(dict.fromkeys(extra))
    return f"{text} {' '.join(extra)}" if extra else text


# --- faq -------------------------------------------------------------------------------------
def covered_hits(found: list, min_score: float | None = None, min_cosine: float | None = None,
                 gate: dict | None = None) -> list:
    """Portão de cobertura: trechos que contam como fonte. Mesma função no agente e na calibração do eval.

    Limiar: argumento (calibração) → COVERAGE_MIN_SCORE / COVERAGE_MIN_COSINE (env) → `gate` (limiares que o
    --choose-retriever calibrou PARA o retriever escolhido; o rag só o entrega se nada caiu) → MIN_SCORE/MIN_COSINE.
    """
    gate = gate or {}
    threshold = min_score if min_score is not None else coverage_min_score(
        gate.get("min_score", domain.active().MIN_SCORE))
    floor = min_cosine if min_cosine is not None else coverage_min_cosine(gate.get("min_cosine", MIN_COSINE))
    best = max((h.cosine for h in found if h.cosine is not None), default=0.0)
    return [h for h in found if h.bm25 >= threshold
            or (h.cosine is not None and h.cosine >= max(floor, best - COSINE_MARGIN))]


def _web_evidence(content) -> tuple[list[str], list[Source]]:
    """Evidência e fontes da busca web: trechos citados (cited_text) e título/data de cada resultado.

    O corpo da página vem cifrado (encrypted_content) e não é legível; o que dá para conferir são as citações
    dos blocos de texto e os metadados dos resultados. Erro da busca chega como objeto, não lista: sem evidência.
    """
    evidence: list[str] = []
    sources: dict[str, Source] = {}
    for block in content:
        kind = getattr(block, "type", None)
        if kind == "web_search_tool_result" and isinstance(getattr(block, "content", None), list):
            for r in block.content:
                if getattr(r, "type", None) == "web_search_result" and getattr(r, "url", None):
                    sources.setdefault(r.url, Source(id=r.url, title=getattr(r, "title", "") or r.url, url=r.url))
                    evidence.append(f"{getattr(r, 'title', '')} ({getattr(r, 'page_age', '') or 's/ data'})")
        elif kind == "text":
            for c in getattr(block, "citations", None) or []:
                if getattr(c, "cited_text", None):
                    evidence.append(f"{getattr(c, 'title', '')}: {c.cited_text}")
                if getattr(c, "url", None):
                    sources.setdefault(c.url, Source(id=c.url, title=getattr(c, "title", "") or c.url, url=c.url))
    return evidence, list(sources.values())


def _lang_tail(ctx: Context) -> str:
    """Diretiva de idioma no FIM da mensagem do turno (onde o modelo mais pesa), não só no prompt de sistema.

    Getnet v4 sobre o motor v5 (01/11/2026, 4 chamadas reais): pergunta em inglês com um termo em português ou
    trechos do site em português saía em português ~50% das vezes; o prompt de sistema em português vencia.
    """
    tail = "\n\n" + grounding.DIRECTIVE.get(ctx.language, grounding.DIRECTIVE["pt"])
    # o que o sistema faz e o que exige confirmação/aprovação: fonte citável em vez de regra lembrada de memória
    tail = "\n\n" + capabilities.prompt_block(ctx.language) + tail
    if tried := ctx.facts.get("attempted_steps"):  # caso em andamento (app/casestate.py): não repetir conselho
        tail = ("\n\nPassos já tentados neste caso, sem sucesso (não repita o mesmo conselho: avance para o próximo "
                "passo ou diga que precisa de um humano): " + " | ".join(tried[-4:])) + tail
    return tail


def _live(ctx: Context, live: live_data.LiveResult) -> AgentResult:
    """Câmbio/clima já consultados no código: o texto bruto da API é a evidência; o LLM (se houver) só redige."""
    template = live.text(ctx.language)
    evidence = [*live.evidence, live.text_pt, live.text_en, f"Hoje é {_today()}"]
    source = Source(id=live.url, title=live.source, url=live.url)
    text = template
    llm = get_llm("agent")
    if llm.enabled:
        framed = (f"<untrusted_content>\n{chr(10).join(live.evidence)}\n{template}\n</untrusted_content>\n\n"
                  f"Pergunta: {ctx.text}{_lang_tail(ctx)}")
        try:
            reply = llm.complete(domain.prompt("live_data.md").format(language=ctx.language, today=_today()),
                                 llm_history(ctx, framed), max_tokens=1024)
            text = reply.text.strip() or template
        except LLMError:
            pass  # template já cita fonte e data
    return AgentResult("faq", "ok", text=text, sources=[source], evidence=evidence,
                       facts={"live_data": live.kind, "web_search": False})


def _general(ctx: Context) -> AgentResult:
    """Pergunta geral: câmbio e clima pela API no código (live_data); o resto pela busca web com LLM; offline sem
    dado ao vivo, resposta honesta sem número inventado."""
    previous = next((m.get("content") for m in reversed(ctx.history or []) if m.get("role") == "user"
                     and (m.get("content") or "").strip() != ctx.text.strip()), None)
    live = live_data.lookup(ctx.text, previous=previous)
    if live:
        return _live(ctx, live)
    llm = get_llm("agent")
    if llm.enabled:
        try:
            reply = llm.create(domain.prompt("general.md").format(language=ctx.language, today=_today()),
                               llm_history(ctx, ctx.text + _lang_tail(ctx)), [WEB_SEARCH], max_tokens=4096)
            text = "".join(b.text for b in reply.content if b.type == "text").strip()
            if text:
                evidence, sources = _web_evidence(reply.content)
                if evidence:  # a data vai no prompt (general.md): dado nosso; busca com erro segue sem evidência
                    evidence.append(f"Hoje é {_today()}")
                return AgentResult("faq", "ok", text=text, sources=sources, facts={"web_search": True},
                                   evidence=evidence)
        except LLMError:
            pass
    text = _t(ctx, "Não tenho acesso a dados em tempo real (clima, câmbio, notícias) neste modo, então não vou "
                   "chutar um número. Consulte uma fonte oficial.",
              "I don't have real-time data (weather, exchange rates, news) in this mode, so I won't guess a "
              "number. Please check an official source.")
    return AgentResult("faq", "ok", text=text, facts={"web_search": False}, evidence=[text])  # template nosso


_PASSAGE_REF = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def cite_ids(text: str, hits: list) -> str:
    """"[1]" / "[1, 2]" (número da passagem no prompt) viram "[<id do documento>]".

    O número só tem sentido dentro do prompt do agente. Quando a resposta do agente vai direto ao cliente (atalho do
    supervisor, plano de 1 passo) ela precisa citar a fonte como a lista `sources` da resposta a nomeia; antes era o
    supervisor LLM que fazia essa troca ao redigir. Número fora do intervalo fica como está.
    """
    def swap(m: re.Match) -> str:
        nums = [int(n) for n in re.split(r"\s*,\s*", m.group(1))]
        if not all(1 <= n <= len(hits) for n in nums):
            return m.group(0)
        return "[" + ", ".join(dict.fromkeys(hits[n - 1].doc.id for n in nums)) + "]"

    return _PASSAGE_REF.sub(swap, text)


# Só o plural, que é como o agente se refere ao conjunto do prompt; "passagem" no singular é palavra comum em pt
# (passagem aérea) e trocá-la mudaria o sentido.
_PROMPT_TERMS = {"passagens": "fontes", "passages": "sources"}
_PROMPT_TERM_RE = re.compile(r"\b(" + "|".join(_PROMPT_TERMS) + r")\b", re.IGNORECASE)


def customer_terms(text: str) -> str:
    """"passagens"/"passages" é o nome que o PROMPT dá aos trechos; para o cliente são as fontes.

    1º ensaio do atalho do supervisor: 15 respostas do faq diziam "The passages don't say..." direto ao cliente; antes
    a redação final do supervisor trocava o termo. Mesmo gênero em pt (as passagens → as fontes); maiúscula preservada.
    """
    def swap(m: re.Match) -> str:
        new = _PROMPT_TERMS[m.group(1).lower()]
        return new.capitalize() if m.group(1)[0].isupper() else new

    return _PROMPT_TERM_RE.sub(swap, text)


def faq_agent(ctx: Context) -> AgentResult:
    if ctx.intent == "general":
        return _general(ctx)
    query = expand_query(" ".join([ctx.text, *ctx.facts.get("query_hints", [])]))
    retriever = get_retriever()
    found = retriever.search(query, k=3)
    hits = covered_hits(found, gate=getattr(retriever, "gate", None))
    if not hits and found and coverage_gate() == "bm25" and not str(retriever.name).startswith("bm25"):
        # O portão do buscador escolhido (cosseno do denso) recusou; o BM25 com o limiar do domínio tem a última
        # palavra antes de "sem fonte". Só o portão do denso fazia o eval de ponta a ponta perder handoff (90,2% →
        # 84,0% no domínio da v4: pergunta de código de recusa ia ao humano com a fonte no índice).
        from .rag import BM25Retriever, get_index

        hits = found if covered_hits(BM25Retriever(get_index()).search(query, k=3)) else []
    if not hits:
        return AgentResult("faq", "insufficient", reason="no_source")
    sources = [Source(id=h.doc.id, title=h.doc.title, url=h.doc.url) for h in hits]
    evidence = [f"{h.doc.title}: {h.doc.text}" for h in hits]
    llm = get_llm("agent")
    if llm.enabled:
        passages = "\n".join(f"[{i}] {h.doc.title} ({h.doc.url}): {h.doc.text}" for i, h in enumerate(hits, 1))
        try:
            part = ctx.facts.get("ask", {}).get("faq")
            question = (f"Mensagem do cliente: {ctx.text}\nParte que cabe a você: {part}"
                        if part and part != ctx.text else f"Pergunta: {ctx.text}")
            # passagens são dado, nunca instrução (injeção indireta): o prompt diz isso e as marca
            framed = f"<untrusted_content>\n{passages}\n</untrusted_content>\n\n{question}{_lang_tail(ctx)}"
            reply = llm.complete(domain.prompt("faq.md").format(language=ctx.language), llm_history(ctx, framed),
                                 max_tokens=4096)
            if "NOT_IN_SOURCES" in reply.text:
                return AgentResult("faq", "insufficient", sources=sources, reason="not_in_sources", evidence=evidence)
            return AgentResult("faq", "ok", text=customer_terms(cite_ids(reply.text.strip(), hits)), sources=sources,
                               evidence=evidence)
        except LLMError:
            pass  # cai no extrativo: resposta pior, mas fundamentada
    # Offline: entre os trechos que passaram no portão, prefere o do idioma da pergunta (site com versão en e pt).
    # Getnet v4: o official em inglês tinha language_acc 50% offline porque o 1º trecho era sempre o pt.
    from .router import detect_language

    top = next((h.doc for h in hits if detect_language(h.doc.text) == ctx.language), hits[0].doc)
    return AgentResult("faq", "ok", sources=sources, evidence=evidence,
                       text=f"{top.text} ({_t(ctx, 'Fonte', 'Source')}: {top.title})")


# --- records ---------------------------------------------------------------------------------
def _records_llm(ctx: Context, llm) -> AgentResult:
    """Loop manual de tool use: o modelo escolhe as tools; o servidor impõe a identidade."""
    part = ctx.facts.get("ask", {}).get("records")
    messages: list = llm_history(ctx, (f"Mensagem do cliente: {ctx.text}\nParte que cabe a você: {part}"
                                       if part and part != ctx.text else ctx.text) + _lang_tail(ctx))
    calls: list[ToolCall] = []
    evidence: list[str] = []
    pending = None
    for _ in range(MAX_TOOL_ROUNDS):
        system = domain.prompt("records.md").format(user_id=ctx.user_id, language=ctx.language)
        resp = llm.create(system, messages, tool_specs())
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            ok = any(c.ok for c in calls) or bool(pending)
            return AgentResult("records", "ok" if ok else "insufficient", text=text, tool_calls=calls,
                               pending_action=pending, reason=None if ok else "no_data", evidence=evidence)
        messages.append({"role": "assistant", "content": resp.content})  # conteúdo inteiro, sem editar
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            result, call = run_tool(block.name, dict(block.input), ctx.user_id, ctx.conversation_id)
            result = memory.with_aggregates(result)  # soma/contagem em código: o redator não faz conta
            calls.append(call)
            evidence.append(json.dumps(result, ensure_ascii=False))
            pending = result.get("action_id") or pending
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False), "is_error": not call.ok})
        messages.append({"role": "user", "content": results})  # todos os resultados numa mensagem só
    return AgentResult("records", "error", tool_calls=calls, reason="tool_loop_limit", pending_action=pending,
                       evidence=evidence)


def records_agent(ctx: Context) -> AgentResult:
    llm = get_llm("agent")
    if llm.enabled:
        try:
            return _records_llm(ctx, llm)
        except LLMError:
            pass  # provedor caiu: mesmo atendimento pelo caminho determinístico
    import sys

    return domain.active().records_offline(ctx, sys.modules[__name__])  # caminho determinístico é do domínio


# --- escalation ------------------------------------------------------------------------------
def escalation_agent(ctx: Context) -> AgentResult:
    reason = ctx.handoff_reason or "user_request"
    summary = f"[{ctx.intent}] {ctx.text[:300]}"
    if ctx.facts.get("escalation_note"):
        summary += f" | supervisor: {ctx.facts['escalation_note']}"
    if ctx.user_summary:  # o operador vê o contexto de conversas anteriores, não só a frase solta
        summary += f" | memória: {ctx.user_summary[:300]}"
    store = get_store()
    is_new = store.ticket_for(ctx.conversation_id, "open") is None
    from .routing import specialty_for  # import tardio: routing lê AGENTS deste módulo

    ticket = store.open_ticket(ctx.conversation_id, ctx.user_id, reason, summary,
                               specialty=specialty_for(ctx.intent, reason))
    if is_new:
        notify_new_ticket(ticket)  # opcional (Telegram); a fila persistida é a fonte da verdade
    text = _t(ctx, f"Encaminhei para um atendente humano (protocolo {ticket['id']}). "
                   "A resposta aparece nesta conversa.",
              f"I've handed this to a human agent (ticket {ticket['id']}). "
              "The reply will show up in this conversation.")
    return AgentResult("escalation", "ok", handoff=Handoff(required=True, reason=reason, ticket_id=ticket["id"]),
                       text=text, evidence=[text])  # template nosso: base dos números citados


AGENTS = {"faq": faq_agent, "records": records_agent, "escalation": escalation_agent}


def __getattr__(attr: str):
    # compatibilidade: `agents.MIN_SCORE` e `agents.ELIGIBLE_STATUS` refletem o domínio ativo
    if attr in ("MIN_SCORE", "ELIGIBLE_STATUS"):
        return getattr(domain.active(), attr)
    raise AttributeError(attr)
