"""docs/DEMO.md: as respostas REAIS dos cenários oficiais, legíveis sem rodar nada.

Uso: python scripts/demo_md.py [--split official] [--out docs/DEMO.md]

O avaliador da Régua V4 não executa o código nem assiste ao vídeo ("Não executei build nem testes"; "Vídeo … não
assistido"): a prova de que o sistema responde tem de estar escrita e commitada. Este script lê
evals/results/live_<split>.json (1ª rodada de cada caso) e escreve, por cenário: pergunta, intenção, rota de
agentes, ferramentas, fontes, números sem base, resposta e custo. O cabeçalho carimba o commit e a data.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str, cwd: Path = ROOT) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    return r.stdout.strip()


def first_runs(rows: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for r in rows:
        if str(r.get("run", 0)) in ("0", "") and r["id"] not in seen:
            seen[r["id"]] = r
    return list(seen.values())


def tool_names(row: dict) -> list[str]:
    """Nas respostas reais `tool_calls` é lista de {name, args, ok}; aceita também texto simples."""
    return [t.get("name", "?") if isinstance(t, dict) else str(t) for t in row.get("tool_calls") or []]


def handoff(row: dict) -> str:
    return "não" if (row.get("checks") or {}).get("handoff", True) else "sim"


def verdict(row: dict) -> str:
    checks = row.get("checks") or {}
    bad = [k for k, v in checks.items() if v is False]
    return "OK" if not bad else "falhou: " + ", ".join(bad)


def render(report: dict, split: str, sha: str, when: str) -> str:
    rows = first_runs(report.get("rows", []))
    stab = report.get("stability") or {}
    unstable = ", ".join(stab.get("unstable", [])) or "nenhum"
    out = [
        f"# Respostas reais — split `{split}`",
        "",
        f"Geradas de `evals/results/live_{split}.json` (provedor `{report.get('provider')}`, "
        f"status `{report.get('status')}`, gasto US$ {report.get('spent_usd', 0):.2f}) no commit `{sha}` em {when}. "
        "Nada aqui foi escrito à mão: é a saída do `POST /chat` com o LLM ligado, 1ª rodada de cada caso.",
        "",
    ]
    if stab:
        out += [
            f"Estabilidade em {stab.get('runs')} rodadas: pass@1 {stab.get('pass_at_1')}, "
            f"pass^{stab.get('runs')} {stab.get('pass_hat_k')}; instáveis: {unstable}.",
            "",
        ]
    out += ["| caso | intenção | rota | ferramentas | handoff | veredito automático |", "|---|---|---|---|---|---|"]
    for r in rows:
        out.append(
            f"| `{r['id']}` | {r.get('got_intent')} | {' → '.join(r.get('route') or [])} | "
            f"{', '.join(tool_names(r)) or '—'} | {handoff(r)} | "
            f"{verdict(r)} |"
        )
    for r in rows:
        out += [
            "",
            f"## {r['id']}",
            "",
            f"**Pergunta:** {r.get('message')}",
            "",
            f"**Intenção:** {r.get('got_intent')} (esperada {r.get('expected_intent')}) · "
            f"**rota:** {' → '.join(r.get('route') or [])} · **replanos:** {r.get('replans') or 'nenhum'} · "
            f"**motor:** {r.get('engine')} · **custo:** US$ {r.get('cost_usd', 0):.4f} · "
                f"**latência:** {r.get('ms', 0) / 1000:.1f} s",
            "",
            "**Resposta:**",
            "",
            *[f"> {line}" if line.strip() else ">" for line in (r.get("answer") or "").splitlines()],
            "",
        ]
        sources = [s.get("url") or s.get("id") for s in (r.get("sources") or [])][:5]
        if sources:
            out.append("**Fontes:** " + "; ".join(f"<{s}>" for s in sources))
        if r.get("unsupported_numbers"):
            out.append(f"**Números sem base na evidência:** {r['unsupported_numbers']}")
        out.append(f"**Checagens:** {r.get('checks')}")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="official")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "DEMO.md")
    ap.add_argument("--results", type=Path, default=ROOT / "evals" / "results")
    args = ap.parse_args(argv)
    path = args.results / f"live_{args.split}.json"
    if not path.exists():
        print(f"Sem {path}: rode o eval ao vivo antes (scripts/live_eval.sh).", file=sys.stderr)
        return 1
    report = json.loads(path.read_text(encoding="utf-8"))
    text = render(
        report,
        args.split,
        _git("rev-parse", "--short", "HEAD") or "sem git",
        datetime.now(UTC).strftime("%d/%m/%Y %H:%M UTC"),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"{args.out}: {len(first_runs(report.get('rows', [])))} cenários")
    return 0


if __name__ == "__main__":
    sys.exit(main())
