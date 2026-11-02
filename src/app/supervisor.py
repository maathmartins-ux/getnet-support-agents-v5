"""Supervisor: executa o plano do router, observa o status de cada agente e replaneja.

Dois motores com a mesma saída (Outcome):
- llm (papel "supervisor": Sonnet 5.5, effort low): loop manual de tool use em que os especialistas
  são tools (faq_agent, records_agent, escalation_agent). O modelo lê cada status (ok|insufficient|error)
  e decide o próximo passo. Várias tool calls na mesma resposta rodam em paralelo.
- table (offline/CI e fallback de qualquer LLMError): o mesmo laço com transições determinísticas
  (PLANS, FALLBACK, ALLOWED, MAX_STEPS). Passos independentes do plano rodam em paralelo.

Replanejamento em dois gatilhos (nos dois motores):
- FALHA: status insufficient/error → FALLBACK do domínio (ex.: escalation);
- ACHADO: o agente devolve `needs` (ex.: records viu "pedido ainda não saiu" → precisa da política de prazo do
  faq). O código insere o passo pedido se a transição estiver em ALLOWED e houver orçamento, e grava em `replans`
  como "<de>:need-><para>". "O LLM propõe, o código dispõe": no motor llm o passo pedido roda mesmo que o modelo
  não o chame, e o resultado vai junto dos tool_result.
Ablação (SUPERVISOR_REPLAN): on (padrão) · no_needs (só reage a falha; mede o ganho do achado) · off (plano fixo).

Orçamento por turno (condição de parada): MAX_MODEL_CALLS, MAX_TURN_USD (o turno inteiro, router incluso) e
NODE_TIMEOUT_S (cada agente). Estourou → entrega a parte já respondida, não roda o resto e abre caso humano com
motivo `budget_exhausted`; os passos que faltaram ficam no caso e rodam quando o operador responder (resume.py).

Caso com o humano: enquanto houver caso aberto na conversa, a mensagem nova é anexada ao caso, leituras seguem e
nenhuma ação de escrita fica proposta (a proposta criada no turno é anulada).

Paralelismo: threads (os agentes fazem I/O — SQLite, HTTP do LLM). Cada thread recebe uma cópia do
contextvars (trace_id, custo do request, span OTel pai). O resultado entra SEMPRE na ordem do plano
(ou dos blocos tool_use), nunca na ordem de término: rota, resposta e eval ficam determinísticos.
Todo desvio do plano vai para `replans`.
"""
from __future__ import annotations

import contextvars
import copy
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field

from . import capabilities, cases, claims, domain
from .agents import AGENTS, AgentResult, Context
from .config import supervisor_fast, supervisor_fast_min_confidence, supervisor_parallel, supervisor_replan
from .llm import LLMError, get_llm
from .observability import METRICS, log, request_model_calls, request_usage, span
from .schemas import Handoff

# PLANS, FALLBACK, ALLOWED, DEPENDS e NO_ESCALATION são do DOMÍNIO (app/domain/<ativo>.py), lidos em tempo de
# chamada: o desafio nunca edita este arquivo. `supervisor.PLANS` continua funcionando (ver __getattr__).
_DOMAIN_NAMES = ("PLANS", "FALLBACK", "ALLOWED", "DEPENDS", "NO_ESCALATION")


def __getattr__(attr: str):
    if attr in _DOMAIN_NAMES:
        return getattr(domain.active(), attr)
    raise AttributeError(attr)


def _d():
    return domain.active()


def no_escalation(ctx: Context) -> bool:
    """Este turno não pode abrir caso humano: intenção do domínio sem escalonamento, ou é a retomada de um caso que
    o humano acabou de responder (reabrir criaria um laço humano → retomada → humano)."""
    return ctx.intent in _d().NO_ESCALATION or bool(ctx.facts.get("resume_of"))


SEQUENTIAL = {"escalation"}  # sempre sozinho e depois dos outros: lê o motivo de quem falhou
MAX_STEPS = 4  # teto de chamadas de agente por turno (plano de 2 + replan + escalonamento)
LOW_CONFIDENCE = 0.4
# Orçamento por turno (env). Turno típico ao vivo: ~6–10 chamadas e US$ 0,01 (v3/v4); o teto pega o laço que
# desanda, não o turno normal. 0 desliga o teto correspondente.
MAX_MODEL_CALLS = 20
MAX_TURN_USD = 0.25
NODE_TIMEOUT_S = 60.0  # agente com LLM e 3 rodadas de tool leva ~10–25 s ao vivo
BUDGET_REASON = "budget_exhausted"
REPLAN_MODES = ("on", "no_needs", "off")
TOOLS = [
    {"name": "faq_agent", "strict": True,
     "description": "Responde dúvidas sobre produto e políticas com RAG e fonte citada. "
                    "Devolve {status, text, sources}.",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["query"],
                      "properties": {"query": {"type": "string", "description": "Pergunta + fatos já obtidos"}}}},
    {"name": "records_agent", "strict": True,
     "description": "Lê registros do PRÓPRIO usuário autenticado e propõe ações que exigem confirmação. "
                    "Pode devolver `needs` (achado que pede outro especialista).",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["request"],
                      "properties": {"request": {"type": "string"}}}},
    {"name": "escalation_agent", "strict": True,
     "description": "Abre caso para atendente humano. Use em pedido explícito, sem fonte, falha repetida ou risco.",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["reason"],
                      "properties": {"reason": {"type": "string"}}}},
]
_TOOL_TO_AGENT = {"faq_agent": "faq", "records_agent": "records", "escalation_agent": "escalation"}
HOLD_TEXT = {
    "pt": "Seu caso {ticket} está com um atendente; anexei esta mensagem a ele. Ações na conta ficam suspensas "
          "até a resposta do atendente.",
    "en": "Your case {ticket} is with a human agent; I've attached this message to it. Account actions are on "
          "hold until the agent replies.",
}


# --- configuração (env lido a cada chamada: testes e eval trocam sem reimportar) ------------------------------
def replan_mode() -> str:
    mode = os.getenv("SUPERVISOR_REPLAN", "on").lower()
    return mode if mode in REPLAN_MODES else "on"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def max_model_calls() -> int:
    return int(_env_float("MAX_MODEL_CALLS", MAX_MODEL_CALLS))


def max_turn_usd() -> float:
    return _env_float("MAX_TURN_USD", MAX_TURN_USD)


def node_timeout_s() -> float:
    return _env_float("NODE_TIMEOUT_S", NODE_TIMEOUT_S)


def budget_exceeded() -> str | None:
    """Qual teto do turno já foi atingido ("model_calls" | "usd"); None = ainda há orçamento."""
    calls, usd = max_model_calls(), max_turn_usd()
    if calls > 0 and request_model_calls() >= calls:
        return "model_calls"
    if usd > 0 and request_usage()["cost_usd"] >= usd:
        return "usd"
    return None


@dataclass
class Outcome:
    results: list[AgentResult] = field(default_factory=list)
    route: list[str] = field(default_factory=list)
    replans: list[str] = field(default_factory=list)
    answer: str | None = None  # resposta final redigida pelo supervisor LLM (None = juntar textos dos agentes)
    engine: str = "table"
    budget: str | None = None  # teto que parou o turno (model_calls | usd | node_timeout)
    deferred: list[str] = field(default_factory=list)  # passos do plano que ficaram para depois do humano


# --- execução de um agente --------------------------------------------------------------------------------
def collect_needs(result: AgentResult, ctx: Context) -> list[dict]:
    """Needs do agente + `needs` nos resultados de tool (evidência JSON) + `domain.needs_for` (opcional).

    Três fontes porque o caminho com LLM do records não monta AgentResult.needs: o domínio deriva o achado do
    resultado da tool. Normaliza e deduplica por agente pedido.
    """
    found = list(result.needs or [])
    for item in result.evidence:
        if item.startswith("{"):
            try:
                data = json.loads(item)
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("needs"), list):
                found += data["needs"]
    hook = getattr(_d(), "needs_for", None)
    if hook is not None:
        found += hook(result, ctx) or []
    out: list[dict] = []
    for need in found:
        if isinstance(need, dict) and need.get("agent") and need["agent"] not in {n["agent"] for n in out}:
            out.append({"agent": str(need["agent"]), "why": str(need.get("why", ""))[:200],
                        "hint": str(need.get("hint", ""))[:300]})
    return out


def _invoke(name: str, ctx: Context) -> AgentResult:
    with span("agent", agent=name) as fields:
        try:
            result = AGENTS[name](ctx)
        except Exception as exc:  # agente quebrado vira status "error": o supervisor replaneja
            result = AgentResult(name, "error", reason=f"exception:{type(exc).__name__}")
        try:
            result.needs = collect_needs(result, ctx)
        except Exception as exc:  # noqa: BLE001 — regra de domínio quebrada não derruba o turno
            log.warning("needs_failed", extra={"extra_fields": {"agent": name, "error": type(exc).__name__}})
            result.needs = []
        fields.update(status=result.status, reason=result.reason)  # quem desistiu e por quê, no log
        return result


def _invoke_timed(name: str, ctx: Context) -> AgentResult:
    """Agente com teto de tempo (NODE_TIMEOUT_S). Estourou → status error, reason node_timeout.

    A thread do agente não é morta (Python não cancela thread): o resultado tardio é descartado. Agente não
    escreve no ctx e escrita de tool só propõe; o pior efeito do atraso é custo, que o teto de US$ limita.
    """
    limit = node_timeout_s()
    if limit <= 0:
        return _invoke(name, ctx)
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(contextvars.copy_context().run, _invoke, name, ctx)
    try:
        return future.result(timeout=limit)
    except FutureTimeout:
        METRICS.inc("node_timeouts_total", agent=name)
        return AgentResult(name, "error", reason="node_timeout")
    finally:
        pool.shutdown(wait=False)


def run_batch(names: list[str], ctx: Context) -> list[AgentResult]:
    """Executa os agentes; em paralelo quando há mais de um. Devolve na ordem de `names`."""
    if len(names) == 1 or not supervisor_parallel():
        return [_invoke_timed(n, ctx) for n in names]
    METRICS.inc("parallel_batches_total", size=str(len(names)))
    with span("parallel", agents=",".join(names)), ThreadPoolExecutor(max_workers=len(names)) as pool:
        futures = [pool.submit(contextvars.copy_context().run, _invoke_timed, n, ctx) for n in names]
        return [f.result() for f in futures]


def _record(name: str, result: AgentResult, ctx: Context, out: Outcome) -> None:
    out.route.append(name)
    out.results.append(result)
    for key, value in result.facts.items():  # fatos acumulam entre agentes, na ordem do plano
        if isinstance(value, dict) and isinstance(ctx.facts.get(key), dict):
            ctx.facts[key].update(value)
        elif isinstance(value, list) and isinstance(ctx.facts.get(key), list):
            ctx.facts[key].extend(value)
        else:
            ctx.facts[key] = value


def next_batch(queue: list[str], budget: int) -> list[str]:
    """Primeiro da fila + os seguintes que não dependem de ninguém do lote. Remove-os da fila."""
    batch = [queue.pop(0)]
    while queue and len(batch) < budget and batch[0] not in SEQUENTIAL and queue[0] not in SEQUENTIAL \
            and not (_d().DEPENDS.get(queue[0], set()) & set(batch)):
        batch.append(queue.pop(0))
    return batch


def next_step(result: AgentResult, done: list[str], intent: str | None = None) -> str | None:
    if not supervisor_replan():  # ablação: plano fixo, falha não desvia
        return None
    d = _d()
    nxt = d.FALLBACK.get(result.agent, "escalation")
    if nxt == "escalation" and intent in d.NO_ESCALATION:
        return None
    return None if nxt in done or nxt not in d.ALLOWED.get(result.agent, set()) else nxt


def accept_need(frm: str, need: dict, ctx: Context, out: Outcome, scheduled: list[str]) -> str | None:
    """O passo pedido por um achado entra no plano? Regras do código, não do modelo.

    Entra se: modo "on"; agente existe e a transição frm→agente está em ALLOWED; ainda não rodou nem está na fila;
    cabe em MAX_STEPS; há orçamento; escalation respeita NO_ESCALATION. A dica vira sub-pergunta do agente.
    """
    agent = need["agent"]
    d = _d()
    if replan_mode() != "on" or agent not in AGENTS or agent not in d.ALLOWED.get(frm, set()) \
            or agent in out.route or agent in scheduled or len(out.route) + len(scheduled) >= MAX_STEPS \
            or (agent == "escalation" and no_escalation(ctx)) or budget_exceeded():
        return None
    ask = need.get("hint") or need.get("why")
    if ask:
        ctx.facts.setdefault("ask", {})[agent] = ask
        if agent in ("faq", "knowledge"):
            ctx.facts.setdefault("query_hints", []).append(ask)
    ctx.facts.setdefault("needs", []).append({"from": frm, **need})
    out.replans.append(f"{frm}:need->{agent}" + (f" ({need['why'][:80]})" if need.get("why") else ""))
    METRICS.inc("replans_total", agent=frm, reason="need", engine=out.engine)
    return agent


def _exhaust(what: str, pending: list[str], ctx: Context, out: Outcome) -> None:
    """Orçamento estourou: guarda o que faltou e leva o caso ao humano (escalation não chama modelo)."""
    out.budget = what
    out.deferred = list(dict.fromkeys(p for p in pending if p != "escalation" and p in AGENTS))
    out.replans.append(f"budget:{what}->escalation")
    METRICS.inc("budget_exhausted_total", kind=what)
    log.warning("budget_exhausted", extra={"extra_fields": {"kind": what, "deferred": out.deferred,
                                                            "calls": request_model_calls()}})
    if "escalation" in out.route or no_escalation(ctx):
        return
    ctx.handoff_reason = BUDGET_REASON
    ctx.facts["escalation_note"] = f"orçamento do turno esgotado ({what}); pendente: {out.deferred or '[]'}"
    _record("escalation", _invoke("escalation", ctx), ctx, out)


# --- motor determinístico ----------------------------------------------------------------------------------
def run_table(plan: list[str], ctx: Context, confidence: float = 1.0) -> Outcome:
    out = Outcome()
    queue = list(plan)
    if confidence < LOW_CONFIDENCE and queue and "escalation" not in queue \
            and not no_escalation(ctx) and supervisor_replan():
        queue.append("escalation")
        ctx.handoff_reason = "low_confidence"
        out.replans.append(f"router:low_confidence({confidence:.2f})->escalation")
    while queue and len(out.route) < MAX_STEPS:
        if (what := budget_exceeded()) is not None:
            _exhaust(what, queue, ctx, out)
            return out
        batch = next_batch(queue, MAX_STEPS - len(out.route))
        results = run_batch(batch, ctx)
        for name, result in zip(batch, results, strict=True):
            _record(name, result, ctx, out)
        timed_out = [n for n, r in zip(batch, results, strict=True) if r.reason == "node_timeout"]
        if timed_out:
            _exhaust("node_timeout", timed_out + queue, ctx, out)
            return out
        for name, result in zip(batch, results, strict=True):
            accepted = [a for need in result.needs if (a := accept_need(name, need, ctx, out, queue))]
            for agent in reversed(accepted):  # o passo pedido roda logo a seguir
                queue.insert(0, agent)
            if result.status == "ok" or accepted:  # achado atendido substitui o fallback da falha
                continue
            nxt = next_step(result, out.route, ctx.intent)
            if nxt == "escalation" and no_escalation(ctx):
                nxt = None
            if not nxt or nxt in queue:  # já agendado por outro agente do mesmo lote
                continue
            ctx.handoff_reason = f"{name}_{result.reason or result.status}"
            if nxt == "escalation":
                _defer_dependents(name, queue, out)
            queue.insert(0, nxt)
            out.replans.append(f"{name}:{result.reason or result.status}->{nxt}")
            METRICS.inc("replans_total", agent=name, reason=result.reason or result.status, engine="table")
    return out


def _defer_dependents(failed: str, queue: list[str], out: Outcome) -> None:
    """O passo `failed` vai ao humano: quem DEPENDE dele (DEPENDS do domínio, direta ou indiretamente) sai da fila e
    espera a resposta do operador, que entra como evidência na retomada (resume.py). Rodar agora seria responder sem
    o fato que faltou (ex.: manual do terminal sem saber o modelo do terminal)."""
    blocked = {failed}
    changed = True
    while changed:
        changed = False
        for step in queue:
            if step not in blocked and _d().DEPENDS.get(step, set()) & blocked:
                blocked.add(step)
                changed = True
    waiting = [q for q in queue if q in blocked and q != failed]
    if waiting:
        queue[:] = [q for q in queue if q not in waiting]
        out.deferred = list(dict.fromkeys([*out.deferred, *waiting]))
        out.replans.append(f"{failed}:escalated->defer{waiting}")


# --- motor LLM ---------------------------------------------------------------------------------------------
def lead_step(plan: list[str], ctx: Context) -> str | None:
    """1º passo do plano que o código roda antes da 1ª volta do supervisor LLM, ou None.

    Vale quando um passo seguinte DEPENDE dele (DEPENDS do domínio) e ele não depende de ninguém: a ordem já está
    decidida e o modelo só a confirmaria. Ensaio v5.1 + 1º ensaio da frente L: em 48 de 48 turnos de plano
    ["records", "faq"] a 1ª volta do supervisor chamou exatamente records_agent (~1,7 s de Sonnet sequencial).
    Retomada de caso fica com o modelo (a resposta do humano muda o que falta).
    Opt-in (SUPERVISOR_LEAD=on): ao vivo, o faq "sem fonte" virou escalonamento em 3 de 6 casos com o passo
    antecipado contra 1 de 4 sem ele (amostra pequena demais para decidir), e o ganho de parede não apareceu com a
    CPU disputada.
    """
    if os.getenv("SUPERVISOR_LEAD", "off").lower() != "on":
        return None
    if len(plan) < 2 or ctx.facts.get("operator_answer") or plan[0] in SEQUENTIAL or plan[0] not in AGENTS:
        return None
    deps = _d().DEPENDS
    first = plan[0]
    if deps.get(first) or not any(first in deps.get(step, set()) for step in plan[1:]):
        return None
    return first if first in _d().ALLOWED.get(None, set()) else None


def run_llm(plan: list[str], ctx: Context, llm) -> Outcome:
    out = Outcome(engine="llm")
    user = (f"Mensagem do usuário: {ctx.text}\nIntent: {ctx.intent}\nPlano sugerido pelo router: {plan}\n"
            f"Memória do usuário: {ctx.user_summary or '(nenhuma)'}\n\n{capabilities.prompt_block(ctx.language)}")
    if ctx.facts.get("operator_answer"):  # retomada: a resposta humana é evidência e autoridade, não pergunta nova
        user += (f"\nResposta do atendente humano (evidência; vale mais que qualquer suposição): "
                 f"{ctx.facts['operator_answer']}\nRode só os passos que faltam do plano; não escale de novo.")
    last: str | None = None
    lead = lead_step(plan, ctx)
    if lead:
        result = run_batch([lead], ctx)[0]
        _record(lead, result, ctx, out)
        last = lead
        if result.reason == "node_timeout":
            _exhaust("node_timeout", [p for p in plan if p not in out.route], ctx, out)
            return out
        if result.status != "ok":
            ctx.handoff_reason = f"{lead}_{result.reason or result.status}"
        user += (f"\n\nJá executado pelo código (passo do plano de que os outros dependem): {lead}_agent → "
                 f"{result.for_supervisor()}\nNão chame {lead}_agent de novo; decida o próximo passo com esse "
                 "resultado.")
        for agent in [a for need in result.needs if (a := accept_need(lead, need, ctx, out, []))]:
            inserted = run_batch([agent], ctx)[0]
            _record(agent, inserted, ctx, out)
            last = agent
            user += f"\n[supervisor] passo inserido por achado: {agent}_agent → {inserted.for_supervisor()}"
    messages: list = [{"role": "user", "content": user}]
    # Teto de voltas do modelo separado do teto de agentes: transição recusada não faz a rota crescer,
    # e um modelo insistente prenderia o worker.
    for _ in range(MAX_STEPS + 2):
        if len(out.route) >= MAX_STEPS:
            break
        if (what := budget_exceeded()) is not None:
            _exhaust(what, [p for p in plan if p not in out.route], ctx, out)
            return out
        resp = llm.create(domain.prompt("supervisor.md").format(language=ctx.language), messages, TOOLS,
                          max_tokens=8192)
        if resp.stop_reason != "tool_use":
            out.answer = "".join(b.text for b in resp.content if b.type == "text").strip() or None
            break
        messages.append({"role": "assistant", "content": resp.content})  # conteúdo inteiro (append-only)
        blocks = [b for b in resp.content if b.type == "tool_use"]
        verdicts: dict[str, dict] = {}
        approved: list[tuple] = []  # (bloco, agente)
        for block in blocks:
            name = _TOOL_TO_AGENT.get(block.name)
            if name is None or name not in _d().ALLOWED[last] or len(out.route) + len(approved) >= MAX_STEPS \
                    or (name == "escalation" and no_escalation(ctx)) \
                    or (not supervisor_replan() and name not in plan):  # ablação: só o plano do router
                verdicts[block.id] = {"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                                      "content": f"transição não permitida: {last}->{block.name}"}
                continue
            approved.append((block, name))
        # escalation (terminal) roda depois dos outros do mesmo turno, sozinha
        batches = [[a for a in approved if a[1] not in SEQUENTIAL], [a for a in approved if a[1] in SEQUENTIAL]]
        remaining = [p for p in plan if p not in out.route]
        notes: list[dict] = []  # passos inseridos pelo código (achado): vão como texto após os tool_result
        for batch in (b for b in batches if b):
            for block, name in batch:
                if name == "escalation":
                    # Motivo livre do modelo vai só para o ticket; métrica usa rótulo fixo (cardinalidade limitada).
                    ctx.handoff_reason = ctx.handoff_reason or (
                        "user_request" if name in remaining else "supervisor_decision")
                    ctx.facts["escalation_note"] = str(block.input.get("reason", ""))[:200]
                elif name == "faq" and block.input.get("query"):
                    ctx.facts.setdefault("query_hints", []).append(str(block.input["query"])[:300])
                # sub-pergunta por agente: em pergunta composta, cada um responde só a sua parte
                ask = block.input.get("query") or block.input.get("request")
                if ask:
                    ctx.facts.setdefault("ask", {})[name] = str(ask)[:300]
                if name not in remaining:
                    out.replans.append(f"{last or 'start'}->{name} (plano: {remaining or '[]'})")
                    METRICS.inc("replans_total", agent=last or "start", reason="llm_decision", engine="llm")
            results = run_batch([name for _, name in batch], ctx)
            for (block, name), result in zip(batch, results, strict=True):
                _record(name, result, ctx, out)
                verdicts[block.id] = {"type": "tool_result", "tool_use_id": block.id,
                                      "content": result.for_supervisor()}
                last = name
                if result.status != "ok" and name != "escalation":
                    ctx.handoff_reason = f"{name}_{result.reason or result.status}"
            timed_out = [n for n, r in zip([n for _, n in batch], results, strict=True) if r.reason == "node_timeout"]
            if timed_out:
                _exhaust("node_timeout", timed_out + [p for p in plan if p not in out.route], ctx, out)
                return out
            # achado → passo inserido pelo código (o modelo não precisa lembrar de pedir)
            called = {n for _, n in approved}
            inserted: list[str] = []
            for (_, name), result in zip(batch, results, strict=True):
                inserted += [a for need in result.needs
                             if need["agent"] not in called and (a := accept_need(name, need, ctx, out, inserted))]
            if inserted:
                for agent, result in zip(inserted, run_batch(inserted, ctx), strict=True):
                    _record(agent, result, ctx, out)
                    last = agent
                    notes.append({"type": "text", "text": f"[supervisor] passo inserido por achado: {agent}_agent "
                                                          f"→ {result.for_supervisor()}"})
        # todos os tool_result numa mensagem só, na ordem dos blocos (texto só depois deles)
        messages.append({"role": "user", "content": [verdicts[b.id] for b in blocks] + notes})
    return out


# --- caso com o humano e plano pendente ------------------------------------------------------------------------
def _hold(ctx: Context, ticket: dict, out: Outcome) -> None:
    """Caso aberto na conversa: anexa a mensagem, anula proposta de escrita do turno e avisa o cliente."""
    from .store import get_store

    cases.attach_note(ticket["id"], ctx.text)
    store = get_store()
    for result in out.results:
        if result.pending_action:  # escrita não fica proposta com o caso no humano: confirmar depois falha
            store.claim_action(result.pending_action, frm="pending", to="on_hold")
            METRICS.inc("actions_on_hold_total")
            result.pending_action, result.text = None, ""
    text = HOLD_TEXT.get(ctx.language, HOLD_TEXT["pt"]).format(ticket=ticket["id"])
    # required=False de propósito: `required` diz "ESTE turno escalou". Caso aberto de turno anterior é só aviso
    # (reason + ticket_id). Com True, toda pergunta depois de uma escalação virava "handoff" e inflava a taxa de
    # escalonamento: ensaio v5 sobre a v4, split memory, handoff 92,3% → 76,9% (q-mem-05 e q-mem-06).
    out.results.append(AgentResult("hold", "ok", text=text, evidence=[text],
                                   handoff=Handoff(required=False, reason="case_open", ticket_id=ticket["id"])))
    if out.answer is not None:
        out.answer = f"{out.answer}\n\n{text}"


def _save_pending(plan: list[str], ctx: Context, out: Outcome) -> None:
    """Turno terminou com o humano e passos do plano não rodaram: ficam no caso para depois da resposta."""
    ticket = next((r.handoff.ticket_id for r in out.results if r.handoff and r.handoff.ticket_id), None)
    if not ticket:
        return
    steps = out.deferred or [p for p in plan if p != "escalation" and p in AGENTS and p not in out.route]
    if steps:
        out.deferred = list(dict.fromkeys(steps))
        cases.save_pending(ticket, ctx, out.deferred)


def run(plan: list[str], ctx: Context, confidence: float = 1.0, prior: list[AgentResult] | None = None) -> Outcome:
    """Um turno. Caso aberto na conversa → modo espera (_hold); caso aberto NESTE turno → guarda o que faltou.

    `prior`: resultados que já existem antes do plano (retomada: o AgentResult "human" com a resposta do operador).
    Os fatos deles entram no contexto dos agentes e eles abrem a rota e os resultados do Outcome.
    """
    held = cases.open_case(ctx.conversation_id)
    seeded = Outcome()
    for result in prior or []:
        _record(result.agent, result, ctx, seeded)
    out = _run(plan, ctx, confidence)
    if seeded.results:
        out.route[:0], out.results[:0] = seeded.route, seeded.results
    if held:
        _hold(ctx, held, out)
    _save_pending(plan, ctx, out)
    return out


def fast_path(plan: list[str], ctx: Context, confidence: float) -> bool:
    """Plano de UM passo com router confiante: a tabela decide e a resposta é a do próprio agente.

    No motor LLM esse turno custa 2 chamadas sequenciais do supervisor (escolher a tool e redigir a resposta final),
    ~4 s por turno no ensaio v5.1, e a redação final só reescrevia o texto do agente (às vezes com frase a mais que o
    verificador de claims cortava depois). Com um passo só não há o que coordenar: falha segue FALLBACK, achado segue
    ALLOWED, igual ao LLM. Ficam no LLM: plano de 2+ passos (compor partes), router incerto e a retomada de caso
    (a resposta do humano muda o que falta fazer).
    """
    return supervisor_fast() and len(plan) == 1 and confidence >= supervisor_fast_min_confidence() \
        and not ctx.facts.get("operator_answer")


OFFER_HUMAN = {"pt": "Se quiser, posso encaminhar sua dúvida a um atendente humano.",
               "en": "If you'd like, I can hand this question to a human agent."}
_MENTIONS_HUMAN = re.compile(r"\b(?:humano|human|atendente|atendimento humano)\b", re.IGNORECASE)


def _offer_human_on_gap(out: Outcome, ctx: Context) -> None:
    """Atalho: resposta do faq que diz que a fonte não cobre parte da pergunta termina oferecendo o humano.

    No motor LLM era a redação final do supervisor que acrescentava a oferta. Sem ela, o 1º ensaio official do atalho
    teve 1 de 30 respostas julgada não útil exatamente por isso (official-04: "não responde nem oferece humano").
    Texto fixo, sem LLM; não vale onde o domínio nunca escala (clima/câmbio) nem quando o turno já abriu caso.
    """
    if no_escalation(ctx) or any(r.handoff for r in out.results):
        return
    for result in out.results:
        if result.agent == "faq" and result.status == "ok" and claims.states_absence(result.text) \
                and not _MENTIONS_HUMAN.search(result.text):
            offer = OFFER_HUMAN.get(ctx.language, OFFER_HUMAN["pt"])
            result.text = f"{result.text.rstrip()}\n\n{offer}"
            result.evidence = [*result.evidence, offer]  # template nosso, como o texto do escalation


def _run(plan: list[str], ctx: Context, confidence: float = 1.0) -> Outcome:
    llm = get_llm("supervisor")
    if llm.enabled and plan and fast_path(plan, ctx, confidence):
        METRICS.inc("supervisor_fast_path_total", agent=plan[0])
        out = run_table(plan, ctx, confidence)
        _offer_human_on_gap(out, ctx)
        return out
    if llm.enabled and plan:
        entry = copy.deepcopy(ctx.facts)  # o que o turno trouxe (dicas, tentativas, resposta humana na retomada)
        try:
            return run_llm(plan, ctx, llm)
        except LLMError:
            METRICS.inc("supervisor_fallback_total")
            # recomeça limpo no motor determinístico: some só o que o motor LLM acumulou, não o que veio de fora
            ctx.facts.clear()
            ctx.facts.update(entry)
            ctx.handoff_reason = None
    return run_table(plan, ctx, confidence)
