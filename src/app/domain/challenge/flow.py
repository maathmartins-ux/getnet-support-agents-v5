"""Domínio do desafio — FLUXO (frente R): taxonomia, planos, FALLBACK, regras do router.

Contrato lido pelo motor: PLANS, FALLBACK, ALLOWED, DEPENDS, NO_ESCALATION, DEFAULT_INTENT,
MULTI_PARTS, states_subject(), clause_intent(), combine().
Teste: tests/test_domain_router.py.
"""
from __future__ import annotations

import re

# --- taxonomia e planos (lidos por router e supervisor) — docs/SPEC.md -------------------------------------
# knowledge→faq · support→records · troubleshoot→records+faq (split dependent: completa só com os 2) ·
# general→faq (live_data/web, nunca escala) · human_request→escalation · multi→faq ∥ records.
PLANS = {
    "knowledge": ["faq"],
    "support": ["records"],
    "troubleshoot": ["records"],  # faq entra pelo `needs` da tool (offline, recusa)
    "general": ["faq"],
    "multi": ["faq", "records"],
    "human_request": ["escalation"],
}
# Status != ok → próximo agente. Sem fonte ou ferramenta quebrada termina em humano.
FALLBACK = {"faq": "escalation", "records": "escalation"}
# Transições permitidas (de → para). None = início. Escalation é terminal.
ALLOWED = {None: {"faq", "records", "escalation"}, "faq": {"records", "escalation"},
           "records": {"faq", "escalation"}, "escalation": set()}
# Quem precisa dos fatos de quem (não roda no mesmo lote). Vazio: o multi roda em paralelo; o troubleshoot já
# põe records antes de faq no plano e o achado (needs) da tool de status vem da frente T.
DEPENDS: dict[str, set[str]] = {}
# Clima e câmbio nunca abrem caso humano (desempate 4).
NO_ESCALATION: set[str] = {"general"}
DEFAULT_INTENT = "knowledge"  # cláusula com assunto do domínio e sem regra
MULTI_PARTS = {"knowledge", "support"}  # o que uma frase-exemplo "multi" do k-NN soma às intenções da mensagem

# --- regras do router offline (desempates da SPEC) ----------------------------------------------------------
_HUMAN = re.compile(r"\b(atendente|humano|pessoa real|falar com algu[eé]m|human|representative|real person"
                    r"|operador|operator|ouvidoria|agent humano)\b", re.IGNORECASE)
# Desempate 1: sintoma de maquininha/transação.
_SYMPTOM = re.compile(r"(n[ãa]o conect\w*|sem sinal|sem conex[ãa]o|off-?line|won'?t connect|not connect\w*"
                      r"|no connection|no signal|can'?t connect|\berr(o|or)\b|recusad\w*|declin\w*|negad\w*"
                      r"|n[ãa]o passa|\bfix\b|como resolvo|o que significa"
                      r"|parou de conectar|lost (its |the )?(internet )?connection|recusaram|refused|\bfailed\b"
                      r"|c[óo]digo \d+|(c[óo]digo|code)\b.{0,25}(signific|mean))", re.IGNORECASE)
# Lista de vendas recusadas é DADO (support), não sintoma: "quais vendas foram recusadas hoje?".
_LISTING = re.compile(r"\b(quais vendas|which sales|list\w* (my )?sales)\b", re.IGNORECASE)
# Desempate 2: dado/ação sobre o próprio cliente.
_SUPPORT = re.compile(r"(\bTX\d+|\bT\d{4}[A-Z]?\b|\bontem\b|\byesterday|quanto vendi|did i sell|quando cai"
                      r"|deposited|quando entra|\b(meu|minha|meus|minhas|my)\s+(\w+\s+)?(vendas?|sales?|dinheiro|money"
                      r"|maquininhas?|terminal|terminais|recebíveis|receivables|extrato)"
                      r"|contest\w*|disput\w*|antecipar|advance my|chamado|support ticket|n[ãa]o reconhe\w*"
                      r"|\bterminal\b)", re.IGNORECASE)
# Desempate 4: mundo fora da Getnet com dado público.
_GENERAL = re.compile(r"\b(weather|forecast|clima|previs[ãa]o do tempo|temperatura|chuva|rain|exchange rate"
                      r"|c[âa]mbio|cota[çc][ãa]o|d[óo]lar|dollar|euro|ptax|not[íi]cias?|news)\b", re.IGNORECASE)
# Desempate 3: "preciso de / posso / funciona" sobre produto ou regra.
_NEED = re.compile(r"\b(do i need|preciso (de|ter)|é preciso|is it necessary)\b", re.IGNORECASE)
_KNOWLEDGE = re.compile(r"\b(como funciona|how does|how do\w*|what is|what's|o que é|quantas parcelas|how many"
                        r"|posso|can i|difference|diferença|qual a taxa|tem maquininha|quanto custa|how much does \w+ cost)\b", re.IGNORECASE)
_FOLLOWUP = re.compile(r"\b(ele|ela|isso|esse|essa|dela|dele|it|that|this one|a outra|the other|what about"
                       r"|e a de|e quando|and when|por qu[eê]|why)\b", re.IGNORECASE)
_DECLINE_CTX = re.compile(r"recusad\w*|declin\w*|negad\w*", re.IGNORECASE)
_PRODUCT = re.compile(r"\b(get smart|get cl[áa]ssica|crediário|link de pagamento|payment link|pix)\b",
                      re.IGNORECASE)


def states_subject(text: str) -> bool:
    """A fala define assunto por REGRA (sem olhar vocabulário)? Usado para achar o assunto da conversa."""
    return bool(_HUMAN.search(text) or _SYMPTOM.search(text) or _SUPPORT.search(text)
                or _GENERAL.search(text))


def _history_text(history: list[dict]) -> str:
    return " ".join(str(m.get("content") or m.get("text") or "") for m in (history or [])[-4:]
                    if m.get("role", "user") == "user")


def clause_intent(text: str, history: list[dict], r) -> str | None:
    """Intenção de UMA cláusula. `r` = módulo app.router (topic_intent, knn_intent, has_subject)."""
    if _HUMAN.search(text):
        return "human_request"
    if _LISTING.search(text):
        return "support"
    if _SYMPTOM.search(text):
        return "troubleshoot"
    if _NEED.search(text) and not re.search(r"\bTX\d+|\bT\d{4}", text):
        return "knowledge"
    if _SUPPORT.search(text):
        return "support"
    if _GENERAL.search(text):
        return "general"
    last = r.topic_intent(history)
    if last in ("support", "troubleshoot", "multi") and _FOLLOWUP.search(text) and not _PRODUCT.search(text):
        # desempate 7: seguimento herda o assunto; "por quê" sobre venda recusada é sintoma
        if _DECLINE_CTX.search(_history_text(history)) and re.search(r"por qu|why|what about|e a de", text, re.I):
            return "troubleshoot"
        return "support"
    if _KNOWLEDGE.search(text):
        return "knowledge"
    if (near := r.knn_intent(text)) is not None:
        return near
    return DEFAULT_INTENT if r.has_subject(text) else None


def combine(intents: set[str]) -> tuple[str, float]:
    """Intenções das cláusulas → (intent da mensagem, confiança)."""
    if "human_request" in intents:
        return "human_request", 0.95
    if MULTI_PARTS <= intents:
        return "multi", 0.8
    for intent, conf in (("troubleshoot", 0.85), ("support", 0.85), ("general", 0.8)):
        if intent in intents:
            return intent, conf
    return DEFAULT_INTENT, 0.7
