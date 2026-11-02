"""Configuração lida do ambiente a cada chamada (testes trocam variáveis sem reimportar)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# USD por 1M de tokens (entrada, saída). Fonte: tabela de preços da Anthropic, consultada em
# 30/10/2026 (cache de 06/10/2026). Confira antes de publicar números de custo; modelo fora da
# tabela é contado com custo 0 e aparece como "unpriced" nas métricas.
PRICES_PER_MTOK = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}

# Papel → (modelo, effort). Cada um troca por env: ROUTER_MODEL, ROUTER_EFFORT, SUPERVISOR_MODEL...
# Effort é declarado sempre (output_config.effort): os padrões mudam entre modelos.
# - router/guardrail: classificação curta com JSON schema → Haiku, low.
# - supervisor: só escolhe o próximo especialista → Sonnet, low (o p95 ao vivo da v2 veio dele em medium).
# - agent: redige com fonte e usa tools → Sonnet, medium.
# - judge: deve ser pelo menos tão capaz quanto o julgado → Opus, medium.
ROLES = {
    "router": ("claude-haiku-5-5", "low"),
    "guardrail": ("claude-haiku-5-5", "low"),
    "supervisor": ("claude-sonnet-5-5", "low"),
    "agent": ("claude-sonnet-5-5", "medium"),
    "judge": ("claude-opus-5-5", "medium"),
    # reranker: só reordena 20 trechos por relevância → Haiku, low. Medido no corpus real da v3 (884 trechos,
    # 45 perguntas): o BM25 acha a fonte no top-20 em 90,4% e no top-3 em 70,8%; o gargalo é a ordem.
    "reranker": ("claude-haiku-5-5", "low"),
    # claims: confere frase a frase contra a evidência (JSON com os índices sem base) → Haiku, low (app/claims.py).
    "claims": ("claude-haiku-5-5", "low"),
}


# Papéis que rodam sem pensamento estendido (ROLE_THINKING=off|adaptive troca por env, ex.: CLAIMS_THINKING=adaptive).
THINKING_OFF: set[str] = set()


def thinking_for(role: str) -> str:
    raw = os.getenv(f"{role.upper()}_THINKING", "").strip().lower()
    if raw in ("off", "adaptive"):
        return raw
    return "off" if role in THINKING_OFF else "adaptive"


def thinking_param(model: str, mode: str, effort: str | None) -> dict | None:
    """Parâmetro `thinking` da API para desligar o pensamento, ou None (padrão do modelo: adaptativo).

    Regras da API (skill claude-api): Haiku 5.5 aceita {"type": "disabled"} com effort até high; Sonnet 5.5 recusa
    "disabled" e desliga com {"type": "between_tools"}, também só até high; Opus 5.5 não desliga (400 em qualquer
    effort). Fora dessas combinações devolve None e o modelo segue no padrão: nunca um pedido que dá 400.
    """
    if mode != "off" or effort in ("xhigh", "max"):
        return None
    if model.startswith("claude-haiku-5-5"):
        return {"type": "disabled"}
    if model.startswith("claude-sonnet-5-5"):
        return {"type": "between_tools"}
    return None


def model_for(role: str) -> str:
    return os.getenv(f"{role.upper()}_MODEL") or ROLES[role][0]


def effort_for(role: str) -> str:
    return os.getenv(f"{role.upper()}_EFFORT") or ROLES[role][1]


def data_dir() -> Path:
    # Caminho explícito: no container o pacote não mora ao lado de data/, e um índice vazio
    # passa despercebido até o smoke test (lição do desafio de 30/10/2026).
    return Path(os.getenv("DATA_DIR", ROOT / "data"))


def db_path() -> Path:
    return Path(os.getenv("DB_PATH", ROOT / "var" / "app.db"))


def database_url() -> str:
    # postgresql://... = Postgres (réplicas em vários hosts; docs/adr/0003-postgres-opcional.md). Qualquer outro valor,
    # ou ausente, mantém o SQLite em DB_PATH: o padrão não pede serviço externo.
    url = os.getenv("DATABASE_URL", "").strip()
    return url if url.startswith(("postgresql://", "postgres://")) else ""


def llm_provider() -> str:
    # "offline" é determinístico e roda no CI sem chave; o modo com LLM nunca é pré-requisito.
    return os.getenv("LLM_PROVIDER", "offline")


def auth_mode() -> str:
    # required: identidade só do Bearer token assinado (padrão seguro).
    # demo: aceita user_id do corpo (payload literal de enunciado) e marca identity_verified=false.
    # Ver docs/adr/0001-auth-mode-demo.md.
    mode = os.getenv("AUTH_MODE", "required").lower()
    return mode if mode in ("demo", "required") else "required"


def auth_secret() -> str:
    return os.getenv("AUTH_SECRET", "dev-secret-change-me")


def operator_token() -> str:
    return os.getenv("OPERATOR_TOKEN", "dev-operator-change-me")


def operator_keys() -> dict[str, str]:
    # "ana:<sha256>,bruno:<sha256>" — só o hash fica na configuração (python -m app.auth operator-key ana).
    pairs = (p.split(":", 1) for p in os.getenv("OPERATOR_KEYS", "").split(",") if ":" in p)
    return {name.strip(): digest.strip() for name, digest in pairs if name.strip() and digest.strip()}


def token_ttl_min() -> int:
    # 60 min: sessão de atendimento típica; o cliente renova. Revogação antecipada via POST /auth/revoke.
    return int(os.getenv("TOKEN_TTL_MIN", "60"))


def auth_issuer() -> str:
    return os.getenv("AUTH_ISSUER", "app")


def auth_audience() -> str:
    return os.getenv("AUTH_AUDIENCE", "app-api")


def action_ttl_min() -> int:
    # Ação de escrita pendente expira: confirmar uma proposta velha executaria algo fora de contexto.
    return int(os.getenv("ACTION_TTL_MIN", "15"))


def sla_minutes(priority: str) -> int:
    # Alvo de resposta humana por prioridade; caso vencido é re-escalonado uma vez (store.escalate_overdue).
    return int(os.getenv("SLA_HIGH_MIN", "120") if priority == "high" else os.getenv("SLA_NORMAL_MIN", "480"))


def rate_limit_per_min() -> int:
    # 30/min por chave: folgado para conversa humana, corta script em loop.
    return int(os.getenv("RATE_LIMIT_PER_MIN", "30"))


def retriever_choice() -> dict:
    # data/retriever.json: escolha MEDIDA por `run_evals --choose-retriever --apply` (retriever, modelos, rerank e
    # os números que a justificam). Ausente ou ilegível = padrões abaixo. Env sempre vence o arquivo.
    path = data_dir() / "retriever.json"
    try:
        return dict(_choice_for(str(path), path.stat().st_mtime))  # cópia: quem chama não altera o cache
    except OSError:
        return {}


@lru_cache(maxsize=4)
def _choice_for(path: str, mtime: float) -> dict:
    import json

    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw.get("choice", {}) if isinstance(raw, dict) else {}


def retriever_name() -> str:
    # bm25 (sem dependência) | hybrid (BM25 + embeddings, RRF) | dense (só embeddings; BM25 só no portão).
    name = (os.getenv("RETRIEVER") or retriever_choice().get("retriever") or "bm25").lower()
    return name if name in ("bm25", "hybrid", "dense") else "bm25"


def rerank_mode() -> str:
    # RERANK=cross|llm|off|auto. auto (padrão) = o rerank da escolha medida (data/retriever.json), senão nenhum.
    # O rerank por LLM só liga pedido (RERANK=llm): no Getnet v4 ele não mudou o Recall@3 e custava latência.
    mode = os.getenv("RERANK", "auto").lower()
    if mode == "auto":
        mode = str(retriever_choice().get("rerank") or "off").lower()
    return mode if mode in ("cross", "llm") else "off"


def rerank_enabled() -> bool:
    return rerank_mode() != "off"


def rerank_model() -> str:
    # Cross-encoder multilíngue (pt/en) suportado pelo fastembed; troca por env ou pela escolha medida.
    return (os.getenv("RERANK_MODEL") or retriever_choice().get("rerank_model")
            or "jinaai/jina-reranker-v2-base-multilingual")


def rerank_pool() -> int:
    # Quantos trechos do base o cross-encoder reordena: o custo cresce linear com isso (um par por trecho).
    return int(os.getenv("RERANK_POOL") or retriever_choice().get("rerank_pool") or 20)


def rerank_chars() -> int:
    # Caracteres de cada trecho que o cross-encoder lê. Bancada da v4 (bge-m3-int8, CPU): 600 caracteres custaram
    # ~1/5 do tempo por par de 1500 e, com pool 20, deram Recall@3 maior (0,777 × 0,764): o fato costuma estar no começo
    # do trecho (o ingest abre cada um com a pergunta da FAQ ou o título da seção).
    return int(os.getenv("RERANK_CHARS") or retriever_choice().get("rerank_chars") or 1500)


def embed_model() -> str:
    # Multilíngue (pt/en) e pequeno; suportado pelo fastembed. Troque por env ou pela escolha medida.
    return (os.getenv("EMBED_MODEL") or retriever_choice().get("embed_model")
            or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def embed_cache_dir() -> Path:
    # Vetores dos trechos por modelo + hash do corpus (rag.doc_vectors): a 2ª subida não recalcula o corpus.
    # Num `git worktree` (frente do relógio), o padrão é o var/embeddings do repositório PRINCIPAL: a chave é modelo +
    # texto, então a frente K vetoriza o corpus uma vez e o check da sessão principal, depois do merge, já o encontra
    # (sem isso, cada worktree vetorizava de novo: 2–4 min de CPU com o e5-large na bancada da v4).
    value = os.getenv("EMBED_CACHE_DIR")
    return Path(value) if value else _main_root(ROOT) / "var" / "embeddings"


def _main_root(root: Path) -> Path:
    """Raiz do repositório principal quando `root` é um worktree (`.git` é um arquivo com
    "gitdir: <main>/.git/worktrees/x"); senão o próprio `root` (repositório normal, container sem .git)."""
    marker = root / ".git"
    try:
        if marker.is_file():
            line = marker.read_text(encoding="utf-8").strip()
            if line.startswith("gitdir:"):
                gitdir = Path(line.split(":", 1)[1].strip())
                gitdir = gitdir if gitdir.is_absolute() else (root / gitdir).resolve()
                if gitdir.parent.name == "worktrees":
                    return gitdir.parent.parent.parent
    except OSError:
        pass
    return root


def supervisor_replan() -> bool:
    # Ablação (eval --ablate-replan): "off" = só o plano inicial do router, sem desvio. Mede quanto o replanejamento
    # vale no eval (mesmos casos com e sem). Produção: sempre "on".
    return os.getenv("SUPERVISOR_REPLAN", "on").lower() != "off"


def supervisor_fast() -> bool:
    # Plano de 1 passo com router confiante vai direto pela tabela (sem o supervisor LLM). "off" volta ao LLM sempre.
    return os.getenv("SUPERVISOR_FAST", "on").lower() != "off"


def supervisor_fast_min_confidence() -> float:
    # Confiança mínima do router para pular o supervisor LLM; abaixo dela o modelo ainda lê o status e replaneja.
    try:
        return float(os.getenv("SUPERVISOR_FAST_MIN_CONFIDENCE", "0.8"))
    except ValueError:
        return 0.8


def supervisor_parallel() -> bool:
    # Agentes independentes do mesmo passo rodam em threads; "false" serializa (depuração).
    return os.getenv("SUPERVISOR_PARALLEL", "true").lower() != "false"


def coverage_min_score(default: float) -> float:
    # Limiar do portão "sem fonte, sem afirmação". Escolha por medida: run_evals --calibrate-gate.
    value = os.getenv("COVERAGE_MIN_SCORE")
    return float(value) if value else default


def coverage_min_cosine(default: float) -> float:
    # Piso de cosseno do portão no denso/híbrido. Muda de escala com o modelo (e5 põe quase tudo em 0,75–0,90):
    # sai calibrado pelo --choose-retriever junto com o retriever escolhido.
    value = os.getenv("COVERAGE_MIN_COSINE")
    return float(value) if value else default


def choice_gate() -> dict:
    # Limiares do portão calibrados para a escolha medida; só valem se o ambiente não trocou retriever, modelo ou
    # rerank (limiar de um retriever aplicado a outro deixaria passar pergunta sem fonte).
    c = retriever_choice()
    same = (retriever_name() == c.get("retriever") and rerank_mode() == (c.get("rerank") or "off")
            and (not c.get("embed_model") or embed_model() == c.get("embed_model"))
            and (not c.get("rerank_model") or rerank_model() == c.get("rerank_model")))
    gate = c.get("gate") if same else None
    return gate if isinstance(gate, dict) else {}


def otel_exporter() -> str | None:
    # console | otlp (extra [otel]). Ausente = só log JSON + /metrics.
    value = os.getenv("OTEL_EXPORTER", "").lower()
    return value if value in ("console", "otlp") else None


# --- credencial e endereço do LLM do APP (não do Claude Code) ---------------------------------------------------
# Kit v3.7 (31/10/2026), sessão da nuvem: o Claude Code reserva ANTHROPIC_API_KEY para si (a variável criada no
# ambiente não chegava aos programas) e exporta ANTHROPIC_BASE_URL apontando para a conexão interna dele, que o SDK
# leria sozinho. O app usa APP_ANTHROPIC_API_KEY (ou ANTHROPIC_API_KEY fora da nuvem) e, na nuvem, a API pública.
PUBLIC_API = "https://api.anthropic.com"


def llm_api_key() -> str | None:
    # espaço, aspas ou quebra de linha coladas junto com a chave na tela de variáveis viram 401 na API
    raw = os.getenv("APP_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""
    return raw.strip().strip("\"'").strip() or None


def llm_base_url() -> str:
    explicit = os.getenv("APP_ANTHROPIC_BASE_URL")
    if explicit:
        return explicit
    if os.getenv("CLAUDE_CODE_REMOTE") == "true":  # o ANTHROPIC_BASE_URL da sessão é do Claude Code, não do app
        return PUBLIC_API
    return os.getenv("ANTHROPIC_BASE_URL") or PUBLIC_API



def llm_first_timeout_s(web: bool = False) -> float:
    """Prazo da 1ª tentativa de cada chamada ao LLM (app/llm.py, `_hedged`); 0 desliga. Com busca web, o dobro."""
    base = float(os.getenv("LLM_FIRST_TIMEOUT_S", "15"))
    return base * 2 if web else base


def coverage_gate() -> str:
    """Quem decide se há fonte: "bm25" (padrão: limiar do domínio sobre o BM25, qualquer que seja o buscador que
    ordena) ou "retriever" (limiares calibrados para o buscador escolhido em data/retriever.json)."""
    return os.getenv("COVERAGE_GATE", "bm25").lower()
