"""Baixa para o cache do fastembed os modelos que a escolha medida usa (data/retriever.json ou env).

Uso: FASTEMBED_CACHE_PATH=/opt/models python scripts/fetch_models.py [--data data]
     python scripts/fetch_models.py --fast > var/fetch_models.log 2>&1 &     # T+0 do relógio, em 2º plano
Roda no build da imagem (EXTRAS=hybrid) e no job de retrieval do CI: o container sobe com --network none e o
eval do CI mede o mesmo modelo que o README cita. Escolha bm25 (ou sem arquivo) = nada a baixar.
--fast: os modelos que o `run_evals --choose-retriever --fast` mede (e5-large + bge-m3-int8, ~2,8 GB), ANTES de
existir escolha: no relógio, a frente K chega ao --choose-retriever com os modelos já no cache.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Os mesmos padrões de src/app/config.py (embed_model, rerank_model): o build da imagem roda sem o src/.
DEFAULT_EMBED = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_CROSS = "jinaai/jina-reranker-v2-base-multilingual"
# Os mesmos de evals/retrieval_eval.py (FAST_EMBED, FAST_CROSS); o teste confere que não divergem.
FAST_EMBED = "intfloat/multilingual-e5-large"
FAST_CROSS = "BAAI/bge-reranker-v2-m3-int8"


def models(data: Path, embed_always: bool = False) -> tuple[str | None, str | None]:
    try:
        choice = json.loads((data / "retriever.json").read_text(encoding="utf-8")).get("choice", {})
    except (OSError, ValueError):
        choice = {}
    retriever = os.getenv("RETRIEVER") or choice.get("retriever") or "bm25"
    rerank = os.getenv("RERANK") or choice.get("rerank") or "off"
    embed = (os.getenv("EMBED_MODEL") or choice.get("embed_model") or DEFAULT_EMBED) \
        if embed_always or retriever in ("hybrid", "dense") else None
    cross = (os.getenv("RERANK_MODEL") or choice.get("rerank_model") or DEFAULT_CROSS) if rerank == "cross" else None
    return embed, cross


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--embed", action="store_true", help="baixa o embedding mesmo com escolha bm25 (imagem hybrid)")
    ap.add_argument("--fast", action="store_true", help="baixa os modelos do --choose-retriever --fast (T+0)")
    args = ap.parse_args(argv)
    embed, cross = (FAST_EMBED, FAST_CROSS) if args.fast else models(args.data, args.embed)
    t0 = time.perf_counter()
    if embed:
        from fastembed import TextEmbedding

        TextEmbedding(embed)
        print(f"embedding: {embed}")
    if cross:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        TextCrossEncoder(cross)
        print(f"cross-encoder: {cross}")
    if not (embed or cross):
        print("escolha sem modelo (bm25): nada a baixar")
    else:
        print(f"MODELOS PRONTOS em {time.perf_counter() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
