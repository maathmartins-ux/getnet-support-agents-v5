"""Tools do domínio Getnet (frente T): totais e datas calculados na tool, isolamento e needs."""
from __future__ import annotations

import pytest


@pytest.fixture
def t(domain_data):
    from app.domain.challenge import tools
    tools._records.cache_clear()
    return tools


def test_kit_example_tools_removed(t):
    assert set(t.TOOLS) == {"get_transactions", "get_settlements", "get_terminal_status", "open_dispute",
                            "request_anticipation", "request_terminal_support"}
    for spec in t.TOOLS.values():
        assert spec["input_schema"]["additionalProperties"] is False
        assert "user_id" not in spec["input_schema"]["properties"]
    assert t.TOOLS["open_dispute"]["risk"] == t.TOOLS["request_anticipation"]["risk"] == "high"
    assert t.TOOLS["request_terminal_support"]["write"] is True


def test_yesterday_total_computed_by_tool(t):
    d = t._get_settlements("cliente1988", "yesterday")["data"]
    assert d["total_brl"] == "R$ 745,50" and d["total"] == "745.50" and d["count"] == 4
    assert {i["transaction_id"] for i in d["settlements"]} == {"TX1001", "TX1002", "TX1003", "TX1005"}


def test_decline_meaning_and_needs(t):
    r = t._get_transactions("cliente1988", "today", "recusada")
    codes = {i["transaction_id"]: i["decline_code"] for i in r["data"]["transactions"]}
    assert codes == {"TX1007": "51", "TX1008": "05"}
    assert "insuficiente" in r["data"]["transactions"][0]["decline_meaning_pt"]
    assert r["needs"][0]["agent"] == "faq"


def test_terminal_offline_needs_faq(t):
    r = t._get_terminal_status("cliente1988")
    assert r["data"]["offline"] == ["T1988B"] and r["needs"][0]["agent"] == "faq"
    assert "needs" not in t._get_terminal_status("cliente1988", "T1988A")


def test_isolation_not_found_indistinguishable(t):
    other = t._get_transactions("cliente2024", transaction_id="TX1006")
    missing = t._get_transactions("cliente2024", transaction_id="TX9999")
    assert other == missing == {"ok": False, "error": "not_found"}
    assert t._get_terminal_status("cliente2024", "T1988B") == {"ok": False, "error": "not_found"}
    assert "TX1004" not in {i["transaction_id"] for i in t._get_transactions("cliente1988")["data"]["transactions"]}


def test_settlement_rules(t):
    from datetime import date
    fri = date(2026, 10, 30)
    assert t.settlement_date(fri, "debito") == date(2026, 11, 2)
    assert t.settlement_date(fri, "pix") == fri
    assert t.settlement_date(fri, "credito") == date(2026, 11, 30)


def test_dispute_only_approved(t):
    assert t.ELIGIBLE_STATUS == {"open_dispute": {"aprovada"}}
