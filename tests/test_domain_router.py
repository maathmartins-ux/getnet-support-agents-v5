"""Roteamento offline do desafio (frente R): intents da SPEC nos casos commitados. Pulado no kit puro."""

import json

import pytest

from app.config import ROOT


def _cases(split: str) -> list[dict]:
    rows = [json.loads(line) for line in (ROOT / "evals" / "cases.jsonl").read_text("utf-8").splitlines()
            if line.strip()]
    return [c for c in rows if c.get("split") == split]


@pytest.mark.parametrize("split", ["official", "replan", "dependent", "parallel", "approval"])
def test_offline_intent_matches_spec(domain_data, split):
    from app import router

    cases = _cases(split)
    assert cases
    wrong = [(c["id"], d.intent) for c in cases
             if (d := router.classify_offline(c["message"], [])).intent != c["expect"]["intent"]]
    assert not wrong, wrong


def test_plans_follow_spec(domain_data):
    from app.domain.challenge import flow

    assert flow.PLANS["troubleshoot"] == ["records", "faq"]
    assert flow.PLANS["general"] == ["faq"]
    assert flow.PLANS["multi"] == ["faq", "records"]
    assert flow.NO_ESCALATION == {"general"}


def test_tiebreakers(domain_data):
    from app import router

    assert router.classify_offline("Preciso de conta para receber Pix?", []).intent == "knowledge"
    assert router.classify_offline("Quero falar com um atendente sobre a minha venda TX1006", []).intent \
        == "human_request"
    assert router.classify_offline("Qual a cotação do dólar hoje?", []).intent == "general"
