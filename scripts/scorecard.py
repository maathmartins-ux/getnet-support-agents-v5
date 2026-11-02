"""Placar honesto: cada número que pesa na nota, com a meta e o status, os ruins junto com os bons.

Uso: python scripts/scorecard.py            (imprime a tabela; o README a recebe pelo bloco `scorecard`)

Lê só o que está commitado em evals/results/ (offline, ao vivo por split, juiz, rótulos humanos). Métrica sem
arquivo sai "não medido", nunca some: quem lê vê o buraco. As metas são as que a avaliação usa para a faixa de
finalista (qualidade semântica: groundedness ≥ 90% nos cenários oficiais; busca: Recall@3 ≥ 0,85 e MRR ≥ 0,80;
memória: pass@1 ≥ 85%; avaliação independente: 2 rotuladores e held-out com ≥ 80 casos).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evals" / "results"


@dataclass(frozen=True)
class Target:
    key: str
    label: str
    goal: float
    unit: str  # "%" (0–100), "frac" (0–1) ou "n" (contagem)
    where: str  # arquivo e campo de onde o número vem


TARGETS = (
    Target("official_grounded", "Juiz: respostas oficiais fundamentadas", 0.90, "frac", "judge.json by_split.official"),
    Target("official_numbers", "Oficiais: números com base na evidência", 95.0, "%", "live_official.json numbers_acc"),
    Target("official_pass_k", "Oficiais: pass^k (todas as rodadas passam)", 0.90, "frac", "live_official.json"),
    Target("memory_pass_1", "Memória ao vivo: pass@1", 0.85, "frac", "live_memory.json stability"),
    Target("memory_numbers", "Memória ao vivo: números com base", 95.0, "%", "live_memory.json numbers_acc"),
    Target("recall3", "Busca: Recall@3", 0.85, "frac", "latest.json retrieval"),
    Target("mrr", "Busca: MRR", 0.80, "frac", "latest.json retrieval"),
    Target("heldout_cases", "Held-out cego: casos", 80, "n", "latest.json metrics.heldout"),
    Target("heldout_intent", "Held-out cego: intenção", 85.0, "%", "latest.json metrics.heldout"),
    Target("raters", "Rotuladores humanos independentes", 2, "n", "human_review.json"),
    Target("judge_kappa", "Juiz × humano: kappa", 0.80, "frac", "judge.json calibration"),
)


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _complete(report: dict | None) -> dict | None:
    """Rodada degradada ou abortada não conta como medida (fica no arquivo `.degraded.json` à parte)."""
    return report if report and report.get("status") in (None, "complete", "ran") else None


def measure(results: Path = RESULTS) -> dict[str, float | None]:
    latest = _load(results / "latest.json") or {}
    official = _complete(_load(results / "live_official.json")) or {}
    memory = _complete(_load(results / "live_memory.json")) or {}
    judge = _load(results / "judge.json") or {}
    human = _load(results / "human_review.json") or {}
    ret = latest.get("retrieval") or {}
    held = (latest.get("metrics") or {}).get("heldout") or {}
    jo = (judge.get("by_split") or {}).get("official") or {}
    om = (official.get("metrics") or {}).get("official") or {}
    mm = (memory.get("metrics") or {}).get("memory") or {}
    return {
        "official_grounded": jo.get("grounded_rate") if not judge.get("judge_unreliable") else None,
        "official_numbers": om.get("numbers_acc"),
        "official_pass_k": (official.get("stability") or {}).get("pass_hat_k"),
        "memory_pass_1": (memory.get("stability") or {}).get("pass_at_1"),
        "memory_numbers": mm.get("numbers_acc"),
        "recall3": ret.get("recall@3"),
        "mrr": ret.get("mrr"),
        "heldout_cases": held.get("cases"),
        "heldout_intent": held.get("intent_acc"),
        "raters": human.get("rotuladores") or (1 if human.get("rotulos") else None),
        "judge_kappa": (judge.get("calibration") or {}).get("cohen_kappa"),
    }


def _fmt(value: float | None, unit: str) -> str:
    if value is None:
        return "não medido"
    if unit == "%":
        return f"{value:.1f}%"
    if unit == "n":
        return f"{value:.0f}"
    return f"{value:.2f}"


def rows(results: Path = RESULTS) -> list[dict]:
    got = measure(results)
    out = []
    for t in TARGETS:
        v = got.get(t.key)
        status = "não medido" if v is None else ("atinge" if v >= t.goal else "abaixo")
        out.append({"key": t.key, "label": t.label, "value": v, "shown": _fmt(v, t.unit),
                    "goal": _fmt(t.goal, t.unit), "status": status, "where": t.where})
    return out


ICON = {"atinge": "✅ atinge", "abaixo": "❌ abaixo", "não medido": "⚠️ não medido"}


def to_markdown(results: Path = RESULTS) -> str:
    table = rows(results)
    lines = ["| métrica | valor | meta | status | de onde vem |", "|---|---:|---:|---|---|"]
    lines += [f"| {r['label']} | {r['shown']} | {r['goal']} | {ICON[r['status']]} | `{r['where']}` |" for r in table]
    weak = [r for r in table if r["status"] != "atinge"]
    if weak:
        lines += ["", f"**Abaixo da meta ou sem medida ({len(weak)} de {len(table)}):** "
                  + "; ".join(f"{r['label']} ({r['shown']})" for r in weak) + "."]
    else:
        lines += ["", f"Todas as {len(table)} metas atingidas nas medidas commitadas."]
    return "\n".join(lines)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    print(to_markdown(Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
