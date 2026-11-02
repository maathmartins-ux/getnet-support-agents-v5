# Arquitetura — Getnet Support Agents (v5)

Descreve só o que o motor (`src/app/*.py`, congelado) faz. A spec é `docs/SPEC.md`; o domínio do desafio fica em
`src/app/domain/challenge/` (`flow.py`, `tools.py`) e `src/app/domain/challenge_prompts/`.

## 1. Agentes e supervisor

```mermaid
flowchart TD
  U["Lojista: POST /chat<br/>src/app/api.py"] --> G["Guardrail de entrada<br/>src/app/guardrails.py check_input"]
  G -- blocked --> B["Recusa sem plano"]
  G --> R["Router: intent + plano<br/>src/app/router.py (KNN + LLM)"]
  R --> S["Supervisor: run / run_table / run_llm<br/>src/app/supervisor.py"]
  S --> K["Knowledge = faq_agent<br/>src/app/agents.py"]
  S --> SP["Support = records_agent<br/>src/app/agents.py + domain/challenge/tools.py"]
  S --> E["Escalation = escalation_agent<br/>src/app/agents.py"]
  SP -- "needs (collect_needs / accept_need)" --> S
  K -- "falha → replanejar (_defer_dependents)" --> S
  S --> P["Enforce: número com evidência, idioma, PII<br/>src/app/pipeline.py _enforce + grounding.py"]
  P --> M["Memória da conversa<br/>src/app/memory.py Ledger + store.py"]
  P --> O["Resposta + trace_id<br/>src/app/observability.py"]
```

- `pipeline.handle` → `_guard_and_route` → `supervisor.run`. O supervisor executa o plano em lotes (`next_batch`,
  `run_batch`; `multi` roda faq ∥ records), aceita `needs` pedidos por um agente (`collect_needs`, `accept_need`),
  e numa falha adia os dependentes e replaneja (`_defer_dependents`, `next_step`). Ablação por `SUPERVISOR_REPLAN`
  (`on`, `no_needs`, `off`).
- `troubleshoot` (sintoma de maquininha ou transação) começa no Support: a tool lê o dado do cliente (terminal offline,
  código de recusa) e devolve `needs` pedindo o Knowledge só quando o achado precisa do manual. Sem o `needs`
  (ablação `no_needs`), dependent-07..10 não completam: o plano fixo não sabe que o manual é preciso.
- Condição de parada por turno: `MAX_MODEL_CALLS`, `MAX_TURN_USD`, `NODE_TIMEOUT_S` (`budget_exceeded`,
  `_invoke_timed`). Estourou → entrega o já respondido e abre caso humano (`_exhaust`).

## 2. RAG e dados ao vivo (Knowledge)

```mermaid
flowchart LR
  Q["Pergunta + histórico<br/>agents.py expand_query (glossary.json)"] --> I["Busca densa e5-large<br/>src/app/rag.py HybridRetriever(dense)"]
  C["Corpus do site oficial<br/>data/knowledge/ via src/app/ingest.py"] --> I
  I --> H["Cobertura mínima<br/>agents.py covered_hits"]
  H -- coberto --> A["Resposta com citação<br/>agents.py cite_ids"]
  H -- sem cobertura --> W["Web restrita / gap → oferta humana<br/>agents.py _web_evidence, supervisor _offer_human_on_gap"]
  L["general: clima, câmbio<br/>src/app/live_data.py (Open-Meteo, BCB PTAX)"] --> A
  A --> N["Número só com evidência<br/>src/app/grounding.py unsupported_numbers"]
```

- O buscador é escolhido por medida (`run_evals --choose-retriever`, `data/retriever.json`; ADR 0004 e ADR 0008).
  Medida deste corpus (341 trechos de 29 URLs; 38 perguntas com fonte, gold de passagens essenciais):

  | buscador | Recall@3 | MRR | p95 por busca | RAM |
  |---|---:|---:|---:|---:|
  | bm25 | 0,579 | 0,504 | 2 ms | 41 MB |
  | **denso e5-large (entrega)** | **0,842** | **0,715** | 235 ms | 1541 MB |
  | denso e5-large + rerank bge-m3-int8 (medido, não adotado) | 0,947 | 0,807 | 2862 ms sob carga | 2368 MB |

  O rerank é o único que passaria as duas metas (Recall@3 ≥ 0,85, MRR ≥ 0,80), mas o p95 medido no relógio passou do
  orçamento de 3 s por busca; ficou o denso, com o piso de cosseno do portão recalibrado 0,88 → 0,82 (ADR 0008).
  Corte por seção e contexto no índice ficam desligados (padrão do kit, medido no ensaio).
- O portão "sem fonte" usa o piso de cosseno do denso (0,82, `data/retriever.json`) e, se ele recusa, o BM25 com o limiar
  do domínio (`MIN_SCORE`); com o piso de 0,82 a recusa de pergunta sem fonte fica com o agente (`NOT_IN_SOURCES`).
- `general` nunca abre caso; número de clima/câmbio só vem da API com data (`live_data.py`).

## 3. Escritas com confirmação e humano no laço (HITL)

```mermaid
sequenceDiagram
  participant L as Lojista
  participant SP as records_agent (agents.py)
  participant A as actions.py run_tool
  participant RK as risk.py classify
  participant OP as Operador (/operator, api.py)
  participant RS as resume.py
  L->>SP: "contesta a TX1006"
  SP->>A: open_dispute(args) — identidade do servidor (auth.py)
  A->>RK: classify (risk high)
  A-->>L: pendente: confirmar? (action_id, expira)
  L->>A: POST /actions/{id}/confirm (confirm_action)
  alt exige aprovação humana
    A->>OP: fila (POST /actions/{id}/approve | reject → decide_action)
  end
  Note over SP,OP: escalation_agent abre handoff (store.py); operador responde em /handoffs/{id}/reply
  OP->>RS: resume_after_human retoma o plano salvo (_save_pending)
  RS-->>L: resposta com a decisão do humano
```

- Nenhuma escrita roda sem confirmação explícita; ação expirada não executa (`actions._expired`).
- SLA do handoff: `api.sla_check` / `POST /handoffs/sla-check`; notificação em `src/app/notify.py`.
