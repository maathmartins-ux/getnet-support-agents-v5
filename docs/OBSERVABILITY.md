# Observabilidade

Fonte: `src/app/observability.py` (congelado). Números de latência, custo e acerto só entram pelos blocos do
`scripts/fill_readme.py` (README e `docs/RESULTS.md`); este arquivo descreve o que existe.

## Sinais
- **Logs JSON** (`JsonFormatter`): cada `span()` vira uma linha com `trace_id` do request (`new_trace_id`,
  `current_trace_id`). PII é mascarada antes de logar (`guardrails.mask_pii` / `mask_output`).
- **Métricas Prometheus** em `GET /metrics` (`Metrics`, `api.py`): latência por span, contadores (ex.:
  `llm_unpriced_calls_total` quando um modelo não tem preço na tabela).
- **Custo por turno**: `record_llm_usage` soma tokens e USD; `request_usage` / `request_model_calls` alimentam o
  orçamento do supervisor (`MAX_TURN_USD`, `MAX_MODEL_CALLS`).
- **OpenTelemetry** opcional: `configure_otel` / `otel_enabled` (exporter por variável de ambiente).
- **Auditoria**: `GET /audit` (trilha de ações e decisões, `store.py`); **analytics**: `GET /analytics`
  (`analytics.py`); **feedback**: `POST /feedback`.
- **Saúde**: `GET /health` (dependências) e `GET /ready` (prontidão para tráfego).

## Como investigar um turno
1. Pegar o `trace_id` da resposta do `/chat` (ou do cabeçalho).
2. Filtrar o log JSON por esse `trace_id`: router → supervisor (lotes, `needs`, replanejamento) → agentes → enforce.
3. Conferir o custo do turno no span final e se houve `budget_exceeded`.

## Alertas sugeridos (piloto)
- Taxa de escalonamento por intenção acima do portão do `docs/PILOT.md`.
- `llm_unpriced_calls_total` > 0 (custo não contabilizado).
- Handoff com SLA vencido (`/handoffs/sla-check`).
- `/ready` falhando em qualquer réplica (ADR 0002).
