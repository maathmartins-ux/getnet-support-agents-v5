"""Validação humana do eval ao vivo: o dono rotula respostas às cegas e o relatório compara com as checagens.

Fluxo (o avaliador da Régua V4 cobrou "validação humana" da qualidade semântica):
  python -m evals.label --export 30   # sorteia (seed fixa, por split); grava evals/human_labels.csv SEM o veredito
  (o dono lê pergunta, resposta e fontes e responde passa/falha; a sessão grava:)
  python -m evals.label --mark official-01=pass official-02=fail:número sem fonte
  python -m evals.label --report           # humano × automático → evals/results/human_review.json

Dois ou mais rotuladores (avaliação independente): cada um rotula a MESMA amostra no seu arquivo, sem ver o do outro:
  python -m evals.label --export 30 --rater ana      # evals/human_labels.ana.csv (mesma seed = mesmas respostas)
  python -m evals.label --mark official-01=fail:numero_inventado --rater ana
O relatório soma: humano × automático por rotulador e humano × humano (concordância e kappa nos ids em comum).
A nota livre depois de ":" começando por um tipo de falha conhecido (FAILURE_TYPES) vira `tipo_falha`, que o juiz
usa para TPR/TNR por tipo.

Veredito automático de uma linha = todas as checagens True. Passa humano = a resposta é correta, fundamentada e no
idioma da pergunta (decisão do dono, sem ver a nota automática). Relatório: concordância, kappa de Cohen, e onde
humano e automático divergem (esses casos mostram o que a checagem automática não enxerga).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
CSV_PATH = HERE / "human_labels.csv"
OUT = RESULTS / "human_review.json"
FIELDS = ["id", "split", "pergunta", "resposta", "fontes", "ferramentas", "humano", "nota", "tipo_falha"]
FAILURE_TYPES = ("invented_number", "unsupported_claim", "stale_source", "offered_unavailable_action",
                 "wrong_language", "leak", "wrong_route", "other")


def csv_path(rater: str | None = None, base: Path = HERE) -> Path:
    """Sem rotulador: o arquivo único de sempre. Com rotulador: um arquivo por pessoa."""
    if not rater:
        return base / "human_labels.csv"
    if not rater.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"nome de rotulador inválido: {rater!r} (use letras, números, - ou _)")
    return base / f"human_labels.{rater.lower()}.csv"


def tool_names(row: dict) -> list[str]:
    return [t.get("name", "?") if isinstance(t, dict) else str(t) for t in row.get("tool_calls") or []]


def auto_pass(row: dict) -> bool:
    checks = row.get("checks") or {}
    return bool(checks) and all(v is not False for v in checks.values())


def load_rows(results: Path = RESULTS) -> list[dict]:
    """Uma linha por caso (a 1ª rodada), de todos os live_*.json."""
    rows, seen = [], set()
    for path in sorted(results.glob("live_*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")).get("rows", []):
            if str(row.get("run", 0)) in ("0", "") and row["id"] not in seen:
                seen.add(row["id"])
                rows.append(row)
    return rows


def sample(rows: list[dict], n: int, seed: int = 7) -> list[dict]:
    """Amostra estratificada: uma passada por split até completar n (seed fixa = reproduzível)."""
    rng = random.Random(seed)
    by_split: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_split[r.get("split", "?")].append(r)
    for lst in by_split.values():
        rng.shuffle(lst)
    picked: list[dict] = []
    while len(picked) < min(n, len(rows)):
        for split in sorted(by_split):
            if by_split[split] and len(picked) < n:
                picked.append(by_split[split].pop())
    rng.shuffle(picked)
    return picked


def export(n: int, results: Path = RESULTS, path: Path = CSV_PATH, seed: int = 7) -> int:
    return _write_csv(path, sample(load_rows(results), n, seed))


def _write_csv(path: Path, rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:  # sem a nota automática: rotulagem às cegas
            w.writerow(
                {
                    "id": r["id"],
                    "split": r.get("split"),
                    "pergunta": r.get("message"),
                    "resposta": r.get("answer"),
                    "fontes": " ".join(r.get("source_ids") or [])[:300],
                    "ferramentas": " ".join(tool_names(r)),
                    "humano": "",
                    "nota": "",
                }
            )
    return len(rows)


def read_labels(path: Path = CSV_PATH) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return [{**{k: "" for k in FIELDS}, **row} for row in csv.DictReader(fh)]


def mark(pairs: list[str], path: Path = CSV_PATH) -> int:
    rows = read_labels(path)
    index = {r["id"]: r for r in rows}
    done = 0
    for pair in pairs:
        key, _, rest = pair.partition("=")
        verdict, _, note = rest.partition(":")
        verdict = verdict.strip().lower()
        if key not in index or verdict not in ("pass", "fail"):
            print(f"ignorado: {pair!r} (use ID=pass ou ID=fail[:nota]; ID tem de estar no CSV)", file=sys.stderr)
            continue
        note = note.strip()
        kind = note.split()[0].strip(".,;") if note else ""
        index[key]["humano"], index[key]["nota"] = verdict, note
        index[key]["tipo_falha"] = kind if verdict == "fail" and kind in FAILURE_TYPES else ""
        done += 1
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return done


def import_page(dump: Path, n: int | None = None, seed: int = 7, results: Path = RESULTS, base: Path = HERE) -> dict:
    """Fichas da página de rotulagem (scripts/label_page.py; a sessão lê `rotulos` com ArtifactData) → um CSV por
    pessoa, pelo mesmo caminho do --mark. Aceita a lista de documentos como vier ({"documents": [...]}, lista de
    {"data": {...}} ou de fichas). Nota: "fail:<tipo> <comentário>", como no --mark."""
    raw = json.loads(dump.read_text(encoding="utf-8"))
    docs = raw.get("documents", raw.get("docs", [])) if isinstance(raw, dict) else raw
    done: dict[str, int] = {}
    for doc in docs:
        data = doc.get("data", doc) if isinstance(doc, dict) else {}
        rater, marks = str(data.get("rater") or "").strip(), data.get("marks") or {}
        if not rater or not marks:
            continue
        path = csv_path(rater, base)
        if not path.exists():  # o CSV nasce das linhas que a página mostrou (com --splits a amostra é outra)
            live = {r["id"]: r for r in load_rows(results)}
            _write_csv(path, [live[i] for i in marks if i in live])
        pairs = []
        for case_id, m in marks.items():
            verdict = m.get("v")
            if verdict not in ("pass", "fail"):
                continue
            note = " ".join(x for x in (m.get("tipo") or "", (m.get("nota") or "").replace(":", " ")) if x)
            pairs.append(f"{case_id}={verdict}" + (f":{note}" if verdict == "fail" and note else ""))
        done[rater] = mark(pairs, path)
    return done


def import_text(text: str, results: Path = RESULTS, base: Path = HERE) -> dict:
    """Plano B da página (quem não entrou com conta do claude.ai): o texto de "Copiar minhas respostas", colado no
    chat ("CONFERENCIA <amostra> <nome>" e uma linha "id=pass|fail|skip[:tipo]" por situação) → o CSV da pessoa."""
    docs, cur = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("CONFERENCIA "):
            parts = line.split(maxsplit=2)
            cur = {"rater": parts[2] if len(parts) > 2 else "", "marks": {}}
            docs.append({"data": cur})
        elif cur is not None and "=" in line:
            case_id, _, rest = line.partition("=")
            verdict, _, kind = rest.partition(":")
            cur["marks"][case_id.strip()] = {"v": verdict.strip(), "tipo": kind.strip()}
    dump = base / ".import_text.json"
    dump.write_text(json.dumps({"documents": docs}, ensure_ascii=False), encoding="utf-8")
    try:
        return import_page(dump, results=results, base=base)
    finally:
        dump.unlink(missing_ok=True)


def kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a for a, _ in pairs) / n
    pb = sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def _vs_auto(labeled: list[dict], auto: dict[str, bool]) -> dict:
    pairs = [(r["humano"] == "pass", auto[r["id"]]) for r in labeled]
    return {
        "rotulos": len(pairs),
        "humano_passa": sum(a for a, _ in pairs),
        "automatico_passa": sum(b for _, b in pairs),
        "concordancia": round(sum(a == b for a, b in pairs) / len(pairs), 3) if pairs else None,
        "kappa": kappa(pairs),
        "divergencias": [
            {"id": r["id"], "humano": r["humano"], "automatico": "pass" if auto[r["id"]] else "fail", "nota": r["nota"]}
            for r in labeled
            if (r["humano"] == "pass") != auto[r["id"]]
        ],
    }


def label_files(base: Path = HERE) -> dict[str, Path]:
    """{rotulador: arquivo}. O arquivo sem nome conta como o rotulador "dono"."""
    files = {}
    if (base / "human_labels.csv").exists():
        files["dono"] = base / "human_labels.csv"
    for path in sorted(base.glob("human_labels.*.csv")):
        files[path.name.split(".")[1]] = path
    return files


def between_humans(by_rater: dict[str, dict[str, bool]]) -> dict | None:
    """Concordância e kappa entre os dois primeiros rotuladores, nos ids que ambos rotularam."""
    names = sorted(by_rater)
    if len(names) < 2:
        return None
    a, b = by_rater[names[0]], by_rater[names[1]]
    common = sorted(set(a) & set(b))
    pairs = [(a[i], b[i]) for i in common]
    return {"rotuladores": names[:2], "comuns": len(common),
            "concordancia": round(sum(x == y for x, y in pairs) / len(pairs), 3) if pairs else None,
            "kappa": kappa(pairs), "divergem": [i for i in common if a[i] != b[i]]}


def report(results: Path = RESULTS, path: Path | None = None, out: Path = OUT, base: Path = HERE) -> dict:
    auto = {r["id"]: auto_pass(r) for r in load_rows(results)}
    files = {"dono": path} if path else label_files(base)
    by_rater: dict[str, dict[str, bool]] = {}
    per: dict[str, dict] = {}
    for name, f in files.items():
        labeled = [r for r in read_labels(f) if r["humano"] in ("pass", "fail") and r["id"] in auto]
        if labeled:
            by_rater[name] = {r["id"]: r["humano"] == "pass" for r in labeled}
            per[name] = _vs_auto(labeled, auto)
    first = per[sorted(per)[0]] if per else _vs_auto([], auto)
    rep = {
        **first,  # campos de sempre: o 1º rotulador (ordem alfabética) × automático
        "rotuladores": len(per),
        "por_rotulador": {k: {x: v[x] for x in ("rotulos", "concordancia", "kappa")} for k, v in per.items()},
        "entre_humanos": between_humans(by_rater),
        "aviso": None if first["rotulos"] >= 20 else f"só {first['rotulos']} rótulos: abaixo de 20 não dá para confiar",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", type=int, metavar="N")
    ap.add_argument("--mark", nargs="+", metavar="ID=pass|fail[:nota]")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--import-page", type=Path, metavar="JSON",
                    help="fichas da página de rotulagem (scripts/label_page.py) → um CSV por pessoa")
    ap.add_argument("--n", type=int, default=None, help="com --import-page: tamanho da amostra exportada")
    ap.add_argument("--import-text", type=Path, metavar="TXT",
                    help='texto de "Copiar minhas respostas" da página (plano B sem conta do claude.ai)')
    ap.add_argument("--rater", help="nome do rotulador (um arquivo por pessoa; mesma amostra para todos)")
    args = ap.parse_args(argv)
    target = csv_path(args.rater)
    if args.export:
        n = export(args.export, path=target, seed=args.seed)
        print(f"{n} respostas em {target.name} (sem veredito automático)")
    if args.mark:
        print(f"{mark(args.mark, path=target)} rótulos gravados em {target.name}")
    if args.import_text:
        print(json.dumps(import_text(args.import_text.read_text(encoding="utf-8")), ensure_ascii=False))
    if args.import_page:
        print(json.dumps(import_page(args.import_page, args.n, args.seed), ensure_ascii=False))
    if args.report:
        rep = report()
        print(json.dumps({k: v for k, v in rep.items() if k != "divergencias"}, ensure_ascii=False))
        for d in rep["divergencias"]:
            print(f"  diverge {d['id']}: humano {d['humano']} × automático {d['automatico']} {d['nota']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
