"""Gold de passagens ESSENCIAIS rotulado às cegas por 2+ rotuladores (kit v5.2).

  python -m evals.essential_gold --export [--k 5] [--dir evals/essential]
      para cada pergunta com fonte do gold (linha sem "no_source": true), junta o top-k do BM25 e o top-k do buscador
      escolhido (sem rerank) e os trechos já citados na linha; embaralha e tira ids, ordem e nota (o rotulador não
      sabe qual trecho a busca pôs em 1º). Grava pool.jsonl (o que o rotulador lê) e key.json (cid → id; ele NÃO lê).
  python -m evals.essential_gold --import labels_A.jsonl labels_B.jsonl [--dir ...] [--out evals/retrieval.d/k.jsonl]
      junta os rótulos ({"qid", "essential": ["c3", ...]}) por consenso (interseção; vazia → união), mede a
      concordância entre rotuladores (Jaccard médio, perguntas idênticas) e escreve `passage_text` em cada linha do
      gold: uma regex por passagem essencial, feita da frase-resposta do trecho (sobrevive a re-ingest; a mesma FAQ
      copiada em outra página casa a mesma regra). Grava report.json ao lado do pool.

Por que (ensaio v5.2 sobre o corpus da v4): o gold "todo trecho relacionado" da v4 media quantos relacionados cabem em
3 vagas (teto 0,971; o melhor buscador parou em 0,78). Com 2 rotuladores cegos (Jaccard 0,81, 31/50 idênticos) o
mesmo buscador acha 0,82–0,85 das passagens essenciais. Rotular VENDO o top-3 inflava o número (ilustração da R2:
0,70 → 1,0 depois de ler o top-3); aqui o rotulador nunca vê a ordem da busca.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
DIR = HERE / "essential"
ANCHOR_CHARS = 90  # regra = começo da frase-resposta mais longa do trecho; curto o bastante para não cruzar um corte


def _gold_path() -> Path:
    from evals import run_evals

    return run_evals.RETRIEVAL


def anchor(text: str) -> str:
    """Regex da frase que responde: a mais longa que não é pergunta, até ANCHOR_CHARS, com espaço flexível."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 30]
    best = sorted([s for s in sents if not s.endswith("?")] or sents or [text.strip()], key=len, reverse=True)[0]
    tokens = re.findall(r"\w+|[^\w\s]", best[:ANCHOR_CHARS])
    if len(tokens) > 3:
        tokens = tokens[:-1]  # o último pode ter sido cortado no meio
    return r"\s*".join(re.escape(t) for t in tokens)


def export(k: int = 10, out_dir: Path | None = None, gold: Path | None = None) -> dict:
    from app.jsonl import read_family
    from app.rag import BM25Retriever, get_index, get_retriever
    from evals.retrieval_eval import _query

    out_dir = out_dir or DIR
    index = get_index()
    by_id = {d.id: d for d in index.docs}
    searchers = [BM25Retriever(index), get_retriever(rerank=None)]
    pool, key = [], {}
    for n, row in enumerate(read_family(gold or _gold_path())):
        if row.get("no_source"):
            continue
        q = row["question"]
        ids = {index.aliases.get(i, i) for i in row.get("relevant") or ()}
        for s in searchers:
            ids |= {h.doc.id for h in s.search(_query(q), k=k)}
        ids = sorted((i for i in ids if i in by_id), key=lambda i: hashlib.md5(f"{q}|{i}".encode()).hexdigest())
        qid = f"q{n:03d}"
        if not ids:  # nenhum candidato: nada a rotular (a pergunta fica como está no gold)
            continue
        key[qid] = {"question": q, "cids": {f"c{j}": i for j, i in enumerate(ids)}}
        pool.append({"qid": qid, "question": q,
                     "candidates": [{"cid": f"c{j}", "title": by_id[i].title, "text": by_id[i].text}
                                    for j, i in enumerate(ids)]})
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pool.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pool), "utf-8")
    (out_dir / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), "utf-8")
    return {"questions": len(pool), "candidates_mean": round(statistics.mean(len(p["candidates"]) for p in pool), 2)
            if pool else 0, "pool": str(out_dir / "pool.jsonl")}


def _groups(path: Path, key: dict) -> dict[str, list[frozenset[str]]]:
    """{"essential": [["c3", "c7"], ["c5"]]}: uma lista por FATO, com todos os trechos que o trazem (a mesma FAQ em
    duas páginas ou em pt e en conta uma vez). Lista plana ("c3", "c5") = cada trecho é um fato."""
    out = {}
    for line in path.read_text("utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            cids = key[row["qid"]]["cids"]
            groups = []
            for g in row.get("essential") or ():
                members = frozenset(cids[c] for c in ([g] if isinstance(g, str) else g) if c in cids)
                if members:
                    groups.append(members)
            out[row["qid"]] = groups
    return out


def _labels(path: Path, key: dict) -> dict[str, set[str]]:
    return {q: set().union(*gs) if gs else set() for q, gs in _groups(path, key).items()}


def consensus(per_rater: list[list[frozenset[str]]]) -> list[frozenset[str]]:
    """Fatos em que os rotuladores concordam: fato de um casa com fato do outro quando têm trecho em comum; o fato
    de consenso aceita qualquer trecho de qualquer um deles. Sem nenhum fato em comum: todos os fatos de todos."""
    first, *rest = per_rater
    agreed = []
    for g in first:
        matches = [next((h for h in other if h & g), None) for other in rest]
        if all(matches):
            agreed.append(frozenset(g.union(*matches)))
    return agreed or [g for gs in per_rater for g in gs]


def agreement(a: dict[str, set[str]], b: dict[str, set[str]]) -> dict:
    both = [q for q in a if q in b]
    jac = [len(a[q] & b[q]) / len(a[q] | b[q]) for q in both if a[q] | b[q]]
    return {"questions": len(both), "jaccard_mean": round(statistics.mean(jac), 3) if jac else None,
            "identical": sum(a[q] == b[q] for q in both)}


def import_labels(paths: list[Path], out: Path | None = None, out_dir: Path | None = None,
                  gold: Path | None = None) -> dict:
    from app.jsonl import read_family
    from app.rag import get_index

    if len(paths) < 2:
        raise ValueError("gold essencial pede 2+ rotuladores (a concordância entre eles é parte da evidência)")
    out_dir = out_dir or DIR
    key = json.loads((out_dir / "key.json").read_text("utf-8"))
    labels = {p.stem: _labels(p, key) for p in paths}
    groups = {p.stem: _groups(p, key) for p in paths}
    names = list(labels)
    pairs = {f"{x}×{y}": agreement(labels[x], labels[y]) for i, x in enumerate(names) for y in names[i + 1:]}
    index = get_index()
    texts = {d.id: d.text for d in index.docs}
    rows = read_family(gold or _gold_path())
    unmatched, empty, written = [], [], 0
    for n, row in enumerate(rows):
        qid = f"q{n:03d}"  # a mesma numeração do export (mesma ordem de leitura do gold)
        if qid not in key or key[qid]["question"] != row["question"]:
            continue
        facts = consensus([groups[n].get(qid, []) for n in names])
        if not facts:
            empty.append(row["question"])
            continue
        rules = []
        for fact in facts:  # um fato = uma regra; cópias do mesmo fato entram como alternativas (qualquer uma vale)
            alts = sorted({anchor(texts[i]) for i in fact if i in texts})
            if alts:
                rules.append(alts[0] if len(alts) == 1 else "(?:" + "|".join(alts) + ")")
        rules = sorted(set(rules))
        unmatched += [r for r in rules if not any(re.search(r, t, re.IGNORECASE) for t in texts.values())]
        row["passage_text"] = rules
        row["essential_by"] = names
        written += 1
    out = out or (gold or _gold_path())
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    report = {"raters": names, "agreement": pairs, "questions_labelled": written,
              "no_essential": empty, "unmatched_rules": unmatched, "gold": str(out)}
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--import", dest="labels", nargs="+", type=Path)
    ap.add_argument("--k", type=int, default=10, help="candidatos de cada buscador (10 cobre o pool do rerank)")
    ap.add_argument("--dir", type=Path, default=None)
    ap.add_argument("--gold", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    if args.export:
        print(json.dumps(export(args.k, args.dir, args.gold), ensure_ascii=False))
    elif args.labels:
        print(json.dumps(import_labels(args.labels, args.out, args.dir, args.gold), ensure_ascii=False, indent=2))
    else:
        ap.error("--export ou --import")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
