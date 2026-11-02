# Modelo de ameaças — Getnet Support Agents (frente Q)

Escopo: API `/chat` (src/app/api.py) → guardrails → router → supervisor → agentes faq (RAG + web/live_data) e
records (tools do CRM fictício) → escalation. Fronteiras de confiança: (1) lojista ↔ API (token, AUTH_MODE);
(2) API ↔ LLM (texto não confiável nos dois sentidos); (3) agente ↔ tools/CRM (identidade do servidor, nunca do
schema); (4) RAG/web ↔ agente (conteúdo externo pode carregar instrução). "Teste" = arquivo que exercita o controle;
"pendente" = controle esperado da frente R/T, medido só após o merge.

## STRIDE
| ameaça | controle | arquivo | teste |
|---|---|---|---|
| S — forjar identidade de outro lojista | token assinado; required ignora `user_id` do corpo; token ruim = 401 | src/app/auth.py, src/app/api.py | tests/test_domain_http.py, tests/test_auth_modes.py |
| T — adulterar parâmetros de escrita (valor, TX) | escrita só com confirmação e `pending_action` | src/app/actions.py | tests/test_hitl.py, tests/test_risk_policy.py |
| R — negar ação feita | trilha de auditoria/observabilidade por turno | src/app/observability.py, src/app/store.py | tests/test_observability_stack.py |
| I — vazar dado do cliente2024 ou PII | isolamento por user_id; "não encontrado" indistinguível; mascaramento de cartão/CPF | src/app/tools.py, src/app/guardrails.py | tests/test_domain_guardrails.py, tests/test_privacy.py |
| D — abuso de volume / custo | rate limit por usuário e IP; orçamento do supervisor | src/app/api.py, src/app/supervisor.py | tests/test_api.py, tests/test_supervisor_needs_budget.py |
| E — modelo chamar tool de risco sem aprovação | política de risco; risk high exige confirmação | src/app/actions.py | tests/test_risk_policy.py, tests/test_claimed_action.py |

## OWASP Top 10 para LLM (2025)
| id | ameaça | controle | arquivo | teste |
|---|---|---|---|---|
| LLM01 | prompt injection direta/indireta/ofuscada | deobfuscate + regex + camada LLM; conteúdo de RAG/web tratado como dado | src/app/guardrails.py | tests/test_domain_guardrails.py (32 casos; 11/32 antes do merge) |
| LLM02 | divulgação de informação sensível | mask_output, isolamento de tools | src/app/guardrails.py, src/app/tools.py | tests/test_privacy.py |
| LLM03 | cadeia de suprimentos | dependências fixadas, ações pinadas | requirements, scripts/pin_actions.sh | tests/test_supply_chain.py |
| LLM04 | envenenamento de dados/corpus | allowlist de fontes na ingestão | src/app/ingest.py, data/sources.json | tests/test_ingest.py, tests/test_domain_corpus.py |
| LLM05 | saída imprópria | grounding e política de números | src/app/grounding.py | tests/test_grounding.py, tests/test_numbers_policy.py |
| LLM06 | agência excessiva | tools com nomes congelados, escrita com confirmação | src/app/actions.py | tests/test_hitl.py |
| LLM07 | vazamento do prompt de sistema | bloqueio de pedido de prompt | src/app/guardrails.py | tests/test_guardrails.py |
| LLM08 | fraquezas de vetor/embedding | recuperação limitada ao corpus oficial; rerank | src/app/rag.py | tests/test_rag.py |
| LLM09 | desinformação | fonte e data obrigatórias; juiz calibrado (48 rótulos) | src/app/grounding.py, evals/judge.py | evals/judge_calibration.d/q.jsonl |
| LLM10 | consumo ilimitado | orçamento por turno, rate limit | src/app/supervisor.py, src/app/api.py | tests/test_supervisor_needs_budget.py |

## OWASP Agentic (ASI01–ASI10)
| id | ameaça | controle | arquivo | teste |
|---|---|---|---|---|
| ASI01 | sequestro de objetivo do agente | guardrail antes do router; RAG/web como dado | src/app/guardrails.py | tests/test_domain_guardrails.py |
| ASI02 | uso indevido de ferramenta | schema sem identidade; confirmação em escrita | src/app/tools.py, src/app/actions.py | tests/test_risk_policy.py |
| ASI03 | abuso de identidade e privilégio | identidade só do servidor; operador com token próprio | src/app/auth.py | tests/test_identity.py, tests/test_domain_http.py |
| ASI04 | cadeia de suprimentos agêntica (MCP, plugins) | servidor MCP local com as mesmas checagens | src/app/mcp_server.py | tests/test_mcp.py |
| ASI05 | execução de código inesperada | nenhuma tool executa código | src/app/tools.py | tests/test_security_asi.py |
| ASI06 | envenenamento de memória/contexto | memória por conversa e por dono | src/app/store.py | tests/test_memory_ledger.py |
| ASI07 | comunicação insegura entre agentes | supervisor centraliza; status ok/insufficient/error | src/app/supervisor.py | tests/test_supervisor.py |
| ASI08 | falhas em cascata | replan com orçamento; escalonamento a humano | src/app/supervisor.py | split replan (evals/cases.jsonl) |
| ASI09 | exploração da confiança humana | resposta não afirma ação não feita | src/app/grounding.py | tests/test_claimed_action.py |
| ASI10 | agente desonesto/fora de controle | canários do juiz; observabilidade | evals/judge.py, src/app/observability.py | tests/test_judge_canaries.py |

## Lacunas medidas
- Regex do motor não pega sinônimo "Disregard prior instructions" (xfail em tests/test_domain_guardrails.py); depende da frente R.
- 21 de 32 guardrails passam a API sem bloqueio antes do merge: risco aberto até a integração remedir.
