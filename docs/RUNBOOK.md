# Runbook — operação

Comandos reais do repositório; nenhum número aqui (medidas ficam nos blocos do `scripts/fill_readme.py`).

## Subir e verificar
| Passo | Comando / endpoint |
|---|---|
| Subir | `docker compose up -d --build` → `/docs`, console do operador em `/operator` |
| Demo com payload literal | `docker compose -f docker-compose.yml -f docker-compose.demo.yml up` (`AUTH_MODE=demo`, ADR 0001) |
| Postgres opcional | `docker compose --profile postgres up -d --build postgres api-pg` (ADR 0003) |
| Saúde | `GET /health`, `GET /ready`, `GET /metrics` |
| Check completo | `python scripts/check.py --docker --scale` |

## Incidentes
| Sintoma | Onde olhar | Ação |
|---|---|---|
| LLM fora / cota esgotada | log com `LLMError` (`src/app/llm.py is_quota_message`) | o pipeline responde pela parte determinística e abre caso humano; trocar chave ou modelo por variável de ambiente, sem deploy |
| Turno lento ou caro | span do supervisor, `budget_exceeded` (`src/app/supervisor.py`) | baixar `MAX_MODEL_CALLS` / `MAX_TURN_USD` / `NODE_TIMEOUT_S` |
| Resposta sem fonte / número suspeito | `grounding.unsupported_numbers` no log do enforce | o número é retirado (`grounding.redact`); revisar o corpus em `data/knowledge/` e reingerir (`src/app/ingest.py`) |
| Replanejamento piorando | ablação `SUPERVISOR_REPLAN=no_needs` ou `off` | rollback de comportamento sem deploy; comparar com `evals/results/ablation_replan*` |
| Fila de handoff parada | `GET /handoffs`, `POST /handoffs/sla-check` | redistribuir operadores (`GET /operators`); notificação em `src/app/notify.py` |
| Ação de risco pendente | `GET /audit`, `POST /actions/{id}/approve` ou `/reject` | operador decide; ação expirada não executa (`actions._expired`) |
| Token vazado | `POST /auth/revoke` (`src/app/auth.py`) | revogar o `jti`; girar o segredo (`src/app/keys.py`, JWKS em `/.well-known/jwks.json`) |
| Pedido LGPD de retenção | `POST /admin/retention/purge` (`store.retention_days`) | purga por idade configurada |
| Réplica fora | `/ready` por instância (cabeçalho de instância, `api.instance_header`) | tirar do balanceador (ADR 0002) |

## Rollback
1. Comportamento: variável de ambiente (`SUPERVISOR_REPLAN`, limites de orçamento, `AUTH_MODE`).
2. Por intenção no piloto: voltar a intenção para `shadow` (`docs/PILOT.md`).
3. Versão: imagem anterior fixada por digest; `docker compose up -d` com a tag anterior.
