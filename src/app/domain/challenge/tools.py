"""Domínio do desafio — FERRAMENTAS (frente T): registro TOOLS e caminho offline do records (Getnet).

Contrato lido pelo motor: TOOLS, ELIGIBLE_STATUS, records(), records_offline(), needs_for().
Teste em tests/test_tools.py. A tool CALCULA totais, datas de liquidação e o significado do código de recusa:
o LLM não soma nem converte (v4 perdeu `numbers` por um total somado pelo modelo).
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from functools import lru_cache

from app.config import data_dir

# --- sistema de registro (adaptador): hoje data/crm/crm.json; em produção, a API do CRM -------------------


@lru_cache(maxsize=4)
def _records(path: str) -> dict:
    return json.loads(open(path, encoding="utf-8").read())


def records() -> dict:
    return _records(str(data_dir() / "crm" / "crm.json"))


def today() -> date:
    return date.today()


DECLINE_CODES = {
    "51": {"pt": "saldo ou limite insuficiente do portador do cartão",
           "en": "insufficient funds or credit limit on the cardholder's card",
           "action_pt": "peça outro cartão ou outra forma de pagamento (Pix, débito)",
           "action_en": "ask for another card or another payment method (Pix, debit)"},
    "05": {"pt": "transação não autorizada pelo banco emissor do cartão",
           "en": "transaction not authorized by the card's issuing bank",
           "action_pt": "o portador deve falar com o banco emissor; tente outro cartão",
           "action_en": "the cardholder should contact the issuing bank; try another card"},
}
METHOD_LABEL = {"debito": ("débito", "debit"), "credito": ("crédito", "credit"), "pix": ("Pix", "Pix")}
# Liquidação: débito D+1 útil, Pix D+0 (agenda padrão), crédito D+30 (ajustado para dia útil).
SETTLEMENT_RULE = {"debito": "D+1 útil", "pix": "D+0", "credito": "D+30"}


def _business(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def settlement_date(sale: date, method: str) -> date:
    if method == "debito":
        return _business(sale + timedelta(days=1))
    if method == "pix":
        return sale
    return _business(sale + timedelta(days=30))


def relative(d: date) -> str:
    delta = (d - today()).days
    return {0: "hoje", -1: "ontem", 1: "amanhã"}.get(delta, f"em {delta} dias" if delta > 0 else f"há {-delta} dias")


def money(cents: int) -> str:
    """R$ 745,50 (pt). A tool devolve também `amount` com ponto (745.50) para respostas em inglês."""
    s = f"{cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _own(kind: str, item_id: str, user_id: str) -> dict | None:
    rec = records().get(kind, {}).get(item_id)
    return rec if rec and rec.get("owner") == user_id else None  # outro dono = inexistente


def _tx_view(tx_id: str, tx: dict) -> dict:
    sale = today() - timedelta(days=tx["days_ago"])
    view = {"transaction_id": tx_id, "date": sale.isoformat(), "when": relative(sale), "method": tx["method"],
            "amount": f"{tx['amount_cents'] / 100:.2f}", "amount_brl": money(tx["amount_cents"]),
            "status": tx["status"], "terminal": tx["terminal"]}
    if tx.get("decline_code"):
        code = DECLINE_CODES.get(tx["decline_code"], {})
        view.update(decline_code=tx["decline_code"], decline_meaning_pt=code.get("pt"),
                    decline_meaning_en=code.get("en"), what_to_do_pt=code.get("action_pt"),
                    what_to_do_en=code.get("action_en"))
    return view


def _mine(user_id: str, days_ago: int | None = None, status: str | None = None) -> list[tuple[str, dict]]:
    out = [(k, v) for k, v in sorted(records().get("transactions", {}).items()) if v["owner"] == user_id]
    if days_ago is not None:
        out = [(k, v) for k, v in out if v["days_ago"] == days_ago]
    if status:
        out = [(k, v) for k, v in out if v["status"] == status]
    return out


_PERIOD = {"type": "string", "enum": ["today", "yesterday", "all"], "description": "Período relativo a hoje"}
_TX = {"type": "string", "pattern": r"^TX\d{4}$", "description": "Código da venda (TX + 4 dígitos)"}
_TERM = {"type": "string", "pattern": r"^T\d{4}[A-Z]$", "description": "Número da maquininha"}
_DAYS = {"today": 0, "yesterday": 1, "all": None}
_FAQ_DECLINE = {"agent": "faq", "why": "venda recusada: o que fazer vem do manual",
                "hint": "código de recusa transação negada"}
_FAQ_OFFLINE = {"agent": "faq", "why": "maquininha offline: os passos vêm do manual de conexão",
                "hint": "maquininha não conecta internet chip Wi-Fi"}


def _get_transactions(user_id: str, period: str = "all", status: str | None = None,
                      transaction_id: str | None = None) -> dict:
    if transaction_id:
        tx = _own("transactions", transaction_id, user_id)
        if not tx:
            return {"ok": False, "error": "not_found"}
        pairs = [(transaction_id, tx)]
    else:
        pairs = _mine(user_id, _DAYS.get(period), status)
    items = [_tx_view(k, v) for k, v in pairs]
    approved = sum(v["amount_cents"] for _, v in pairs if v["status"] == "aprovada")
    data = {"period": period, "transactions": items, "count": len(items),
            "approved_total": f"{approved / 100:.2f}", "approved_total_brl": money(approved),
            "declined": [i["transaction_id"] for i in items if i["status"] == "recusada"]}
    out = {"ok": True, "data": data}
    if data["declined"]:
        out["needs"] = [dict(_FAQ_DECLINE)]
    return out


def _get_settlements(user_id: str, period: str = "yesterday") -> dict:
    items = []
    by_date: dict[str, int] = {}
    for k, v in _mine(user_id, _DAYS.get(period), "aprovada"):
        sale = today() - timedelta(days=v["days_ago"])
        pay = settlement_date(sale, v["method"])
        items.append({"transaction_id": k, "method": v["method"], "amount": f"{v['amount_cents'] / 100:.2f}",
                      "amount_brl": money(v["amount_cents"]), "rule": SETTLEMENT_RULE[v["method"]],
                      "settlement_date": pay.isoformat(), "settlement_when": relative(pay)})
        by_date[pay.isoformat()] = by_date.get(pay.isoformat(), 0) + v["amount_cents"]
    total = sum(by_date.values())
    return {"ok": True, "data": {"period": period, "settlements": items, "count": len(items),
                                 "total": f"{total / 100:.2f}", "total_brl": money(total),
                                 "by_date": {d: money(c) for d, c in sorted(by_date.items())}}}


def _get_terminal_status(user_id: str, terminal_id: str | None = None) -> dict:
    terms = records().get("terminals", {})
    if terminal_id:
        if not _own("terminals", terminal_id, user_id):
            return {"ok": False, "error": "not_found"}
        ids = [terminal_id]
    else:
        ids = sorted(k for k, v in terms.items() if v["owner"] == user_id)
    items = [{"terminal_id": k, **{f: x for f, x in terms[k].items() if f != "owner"}} for k in ids]
    offline = [i["terminal_id"] for i in items if i["status"] == "offline"]
    out = {"ok": True, "data": {"terminals": items, "count": len(items), "offline": offline}}
    if offline:
        out["needs"] = [dict(_FAQ_OFFLINE)]
    return out


def _open_dispute(user_id: str, transaction_id: str) -> dict:
    if not _own("transactions", transaction_id, user_id):
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "data": {"transaction_id": transaction_id, "status": "dispute_opened"}}


def _request_anticipation(user_id: str, method: str = "credito") -> dict:
    total = sum(v["amount_cents"] for _, v in _mine(user_id, None, "aprovada") if v["method"] == method)
    return {"ok": True, "data": {"method": method, "amount_brl": money(total), "status": "anticipation_requested"}}


def _request_terminal_support(user_id: str, terminal_id: str) -> dict:
    if not _own("terminals", terminal_id, user_id):
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "data": {"terminal_id": terminal_id, "status": "support_ticket_opened"}}


def _schema(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or [], "additionalProperties": False}


TOOLS = {
    "get_transactions": {"description": "Vendas do cliente autenticado com total aprovado, data relativa e "
                                        "significado do código de recusa.", "write": False,
                         "input_schema": _schema({"period": _PERIOD, "status": {"type": "string",
                                                  "enum": ["aprovada", "recusada"]}, "transaction_id": _TX}),
                         "fn": _get_transactions},
    "get_settlements": {"description": "Quando cai o dinheiro das vendas aprovadas: data de cada venda e total.",
                        "write": False, "input_schema": _schema({"period": _PERIOD}), "fn": _get_settlements},
    "get_terminal_status": {"description": "Status das maquininhas do cliente (online/offline, conexão, sinal).",
                            "write": False, "input_schema": _schema({"terminal_id": _TERM}),
                            "fn": _get_terminal_status},
    "open_dispute": {"description": "Contesta uma venda aprovada. Exige confirmação e aprovação de um atendente.",
                     "write": True, "risk": "high",
                     "input_schema": _schema({"transaction_id": _TX}, ["transaction_id"]), "fn": _open_dispute},
    "request_anticipation": {"description": "Pede antecipação de recebíveis. Exige confirmação e aprovação.",
                             "write": True, "risk": "high",
                             "input_schema": _schema({"method": {"type": "string", "enum": ["credito"]}}),
                             "fn": _request_anticipation},
    "request_terminal_support": {"description": "Abre chamado técnico para a maquininha. Exige confirmação.",
                                 "write": True, "input_schema": _schema({"terminal_id": _TERM}, ["terminal_id"]),
                                 "fn": _request_terminal_support},
}
# Contestar só venda aprovada (v3: contestava a ÚLTIMA, mesmo recusada).
ELIGIBLE_STATUS: dict[str, set[str]] = {"open_dispute": {"aprovada"}}


def needs_for(result, ctx) -> list[dict]:
    """Caminho com LLM: deriva `needs` dos resultados de tool do records (offline/recusa → faq)."""
    if result.agent != "records":
        return []
    for item in result.evidence:
        try:
            data = json.loads(item)
        except ValueError:
            continue
        if isinstance(data, dict) and isinstance(data.get("needs"), list) and data["needs"]:
            return [dict(n) for n in data["needs"]]
    return []


# --- caminho offline do agente records (sem LLM) ------------------------------------------------------------
_TXID = re.compile(r"\bTX\d{4}\b", re.IGNORECASE)
_TERMID = re.compile(r"\bT\d{4}[AB]\b", re.IGNORECASE)
_DISPUTE = re.compile(r"contest|dispute|n[aã]o reconhe|chargeback", re.IGNORECASE)
_ANTICIP = re.compile(r"antecip|advance|anticipat", re.IGNORECASE)
_TICKET = re.compile(r"chamado|ticket|suporte t[eé]cnico|technical support", re.IGNORECASE)
_SETTLE = re.compile(r"\b(cai|caem|cair|dep[oó]sit\w*|liquida\w*|deposited|paid out)\b", re.IGNORECASE)
_TERMINAL = re.compile(r"maquininha|m[aá]quina|terminal|card machine|card reader|conect|connect|wi-?fi|sinal|"
                       r"signal|offline|off-line|cl[aá]ssica|smart", re.IGNORECASE)
_DECLINE = re.compile(r"recus|negad|declin|denied", re.IGNORECASE)
_AMOUNT = re.compile(r"\b(\d{2,4})(?:[.,]\d{2})?\b")
_OTHER = re.compile(r"\b(outra|other)\b", re.IGNORECASE)
_EXPLAIN = re.compile(r"\b(what is|o que [eé]|como funciona|how does)\b", re.IGNORECASE)


def _texts(ctx) -> list[str]:
    return [ctx.text] + [m["content"] for m in reversed(ctx.history)] + [ctx.conversation_digest or ""]


def _find(rx, ctx) -> str | None:
    for text in _texts(ctx):
        if found := rx.search(text or ""):
            return found.group(0).upper()
    return None


def _here(rx, text: str) -> str | None:
    found = rx.search(text)
    return found.group(0).upper() if found else None


def _tx_by_amount(text: str, user_id: str) -> str | None:
    for n in _AMOUNT.findall(text):
        for k, v in _mine(user_id):
            if v["amount_cents"] == int(n) * 100:
                return k
    return None


def records_offline(ctx, a):
    """Atendimento determinístico do records. `a` = módulo app.agents (AgentResult, run_tool, _t)."""
    AgentResult, run_tool, t = a.AgentResult, a.run_tool, a._t
    uid, text = ctx.user_id, ctx.text
    subjects = (_DISPUTE, _ANTICIP, _TICKET, _SETTLE, _TERMINAL, _DECLINE, _TXID, _TERMID)
    # seguimento curto sem assunto ("And how do I fix it?") herda o assunto da fala anterior do cliente
    prev = next((m["content"] for m in reversed(ctx.history) if m.get("role") == "user"), "")
    s = text if any(rx.search(text) for rx in subjects) else f"{text} {prev}"
    calls: list = []
    ev: list[str] = []

    def call(name: str, args: dict) -> dict:
        result, c = run_tool(name, args, uid, ctx.conversation_id)
        calls.append(c)
        ev.append(json.dumps(result, ensure_ascii=False))
        return result

    def done(text_pt: str, text_en: str, **kw):
        return AgentResult("records", "ok", tool_calls=calls, evidence=ev, text=t(ctx, text_pt, text_en), **kw)

    def pending(result: dict, what_pt: str, what_en: str, facts: dict):
        if result.get("error") == "not_found":
            return done("Não encontrei esse registro na sua conta.", "I couldn't find that record in your account.",
                        facts=facts)
        aid, hi = result.get("action_id"), result.get("risk") == "high"
        return done(f"Para {what_pt}, confirme a ação {aid}."
                    + (" Depois da sua confirmação, um atendente aprova." if hi else "") + " Nada foi feito ainda.",
                    f"To {what_en}, confirm action {aid}."
                    + (" After you confirm, a human agent approves it." if hi else "") + " Nothing has been done yet.",
                    pending_action=aid, facts=facts)

    if _DISPUTE.search(text):
        tx = _here(_TXID, text) or _tx_by_amount(text, uid) or _find(_TXID, ctx)
        if not tx:  # sem venda citada: a única aprovada de hoje que o cliente pode não reconhecer é a maior
            today_ok = _mine(uid, 0, "aprovada")
            tx = max(today_ok, key=lambda kv: kv[1]["amount_cents"])[0] if today_ok else None
        if not tx:
            return done("Qual venda você quer contestar?", "Which sale do you want to dispute?")
        found = call("get_transactions", {"transaction_id": tx})
        if found.get("ok") and a.latest_eligible(found["data"]["transactions"], "open_dispute") is None:
            return done(f"A venda {tx} foi recusada: não há o que contestar. Nada foi feito.",
                        f"Sale {tx} was declined: there is nothing to dispute. Nothing was done.",
                        facts={"transaction_id": tx, "ineligible": "open_dispute"})
        return pending(call("open_dispute", {"transaction_id": tx}), f"contestar a venda {tx}",
                       f"dispute sale {tx}", {"transaction_id": tx})
    if _ANTICIP.search(s) and not _EXPLAIN.search(text):
        return pending(call("request_anticipation", {"method": "credito"}),
                       "antecipar seus recebíveis do crédito", "advance your credit receivables", {})
    if _TICKET.search(s):
        term = _find(_TERMID, ctx) or (call("get_terminal_status", {})["data"]["offline"] or [None])[0]
        if not term:
            return done("Para qual maquininha?", "For which terminal?")
        return pending(call("request_terminal_support", {"terminal_id": term}),
                       f"abrir o chamado técnico da maquininha {term}",
                       f"open a technical support ticket for terminal {term}", {"terminal_id": term})
    if _SETTLE.search(text) or re.search(r"\bwhen will\b", text, re.I):
        d = call("get_settlements", {"period": "today" if re.search(r"\b(hoje|today)\b", text, re.I)
                                     else "yesterday"})["data"]
        tx = _here(_TXID, text) or _tx_by_amount(text, uid) or (
            _tx_by_amount(" ".join(m["content"] for m in ctx.history[-2:]), uid) if ctx.history else None)
        rows = [i for i in d["settlements"] if i["transaction_id"] == tx] or d["settlements"]
        pt = "; ".join(f"{i['transaction_id']} ({METHOD_LABEL[i['method']][0]}, {i['amount_brl']}): {i['rule']}, "
                       f"cai em {i['settlement_date']} ({i['settlement_when']})" for i in rows)
        en = "; ".join(f"{i['transaction_id']} ({METHOD_LABEL[i['method']][1]}, R$ {i['amount']}): {i['rule']}, "
                       f"deposited on {i['settlement_date']}" for i in rows)
        return done(f"Total das vendas aprovadas: {d['total_brl']}. {pt}.",
                    f"Total of approved sales: R$ {d['total']}. {en}.", facts={"total": d["total_brl"]})
    tx = _here(_TXID, text) or _tx_by_amount(text, uid)
    if _DECLINE.search(s) or tx:
        r = call("get_transactions", {"transaction_id": tx} if tx else {"period": "all", "status": "recusada"})
        if not r.get("ok"):
            return done("Não encontrei essa venda na sua conta.", "I couldn't find that sale in your account.")
        items = r["data"]["transactions"]
        pt = "; ".join(f"{i['transaction_id']} ({i['amount_brl']}, {i['when']}) " + (
            f"recusada, código {i['decline_code']}: {i['decline_meaning_pt']}; {i['what_to_do_pt']}"
            if i.get("decline_code") else i["status"]) for i in items)
        en = "; ".join(f"{i['transaction_id']} (R$ {i['amount']}) " + (
            f"declined, code {i['decline_code']}: {i['decline_meaning_en']}; {i['what_to_do_en']}"
            if i.get("decline_code") else i["status"]) for i in items)
        return done(pt + ".", en + ".", needs=r.get("needs", []),
                    facts={"transactions": [i["transaction_id"] for i in items]})
    if _TERMINAL.search(s) or _OTHER.search(text):
        term = _here(_TERMID, text)
        if not term and _OTHER.search(text) and (prev := _find(_TERMID, ctx)):
            mine = call("get_terminal_status", {})["data"]["terminals"]
            term = next((i["terminal_id"] for i in mine if i["terminal_id"] != prev), None)
        r = call("get_terminal_status", {"terminal_id": term} if term else {})
        if not r.get("ok"):
            return done("Não encontrei essa maquininha na sua conta.", "I couldn't find that terminal in your account.")
        items = r["data"]["terminals"]
        pt = "; ".join(f"{i['terminal_id']} {i['model']} ({i['connection']}): {i['status']}" + (
            f" há {i['offline_minutes']} min, {i['signal']}" if i["status"] == "offline" else "") for i in items)
        en = "; ".join(f"{i['terminal_id']} {i['model']} ({i['connection']}): {i['status']}" + (
            f" for {i['offline_minutes']} min, no signal" if i["status"] == "offline" else "") for i in items)
        return done(pt + ".", en + ".", needs=r.get("needs", []),
                    facts={"terminals": [i["terminal_id"] for i in items]})
    period = "yesterday" if re.search(r"\b(ontem|yesterday)\b", text, re.I) else (
        "today" if re.search(r"\b(hoje|today)\b", text, re.I) else "all")
    d = call("get_transactions", {"period": period})["data"]
    pt = ", ".join(f"{i['transaction_id']} {i['amount_brl']} ({i['status']}, {i['when']})" for i in d["transactions"])
    en = ", ".join(f"{i['transaction_id']} R$ {i['amount']} ({i['status']})" for i in d["transactions"])
    return done(f"Vendas: {pt}. Total aprovado: {d['approved_total_brl']}.",
                f"Sales: {en}. Approved total: R$ {d['approved_total']}.", facts={"total": d["approved_total_brl"]})
