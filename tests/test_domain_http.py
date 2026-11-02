"""Frente Q — official do desafio via HTTP em AUTH_MODE required e demo; token ruim = 401.

Escrito contra a SPEC (intents knowledge/support/troubleshoot/general); a rota certa depende das frentes R e T e
pode falhar até o merge. Pulado no kit puro (sem domínio do desafio).
"""
import json

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.auth import issue_token
from app.config import ROOT

client = TestClient(app)
USER = "cliente1988"
OFFICIAL = [json.loads(line) for line in (ROOT / "evals" / "cases.jsonl").read_text("utf-8").splitlines()
            if line.strip() and json.loads(line)["split"] == "official"]


def bearer(user=USER):
    return {"Authorization": f"Bearer {issue_token(user)}"}


def test_has_ten_official():
    assert len(OFFICIAL) == 10


@pytest.mark.parametrize("case", OFFICIAL, ids=[c["id"] for c in OFFICIAL])
def test_official_required_mode(domain_data, case):
    r = client.post("/chat", json={"message": case["message"]}, headers=bearer())
    assert r.status_code == 200
    body = r.json()
    assert body["answer"].strip()
    assert body["user_id"] == USER and body["identity_verified"] is True


@pytest.mark.parametrize("case", OFFICIAL[:3], ids=[c["id"] for c in OFFICIAL[:3]])
def test_official_demo_mode(domain_data, monkeypatch, case):
    monkeypatch.setenv("AUTH_MODE", "demo")
    r = client.post("/chat", json={"message": case["message"], "user_id": USER})
    assert r.status_code == 200
    assert r.json()["identity_verified"] is False


@pytest.mark.parametrize("mode", ["required", "demo"])
def test_bad_token_is_401(domain_data, monkeypatch, mode):
    monkeypatch.setenv("AUTH_MODE", mode)
    headers = {"Authorization": "Bearer cliente1988.assinatura-forjada"}
    r = client.post("/chat", json={"message": OFFICIAL[0]["message"], "user_id": USER}, headers=headers)
    assert r.status_code == 401


def test_required_ignores_body_identity(domain_data):
    assert client.post("/chat", json={"message": "Quanto vendi ontem?", "user_id": USER}).status_code == 401
