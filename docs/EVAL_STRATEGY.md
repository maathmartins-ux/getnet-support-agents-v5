# Estratégia de avaliação (frente Q)

## O que mede cada split (casos da frente Q em `evals/cases.d/q.jsonl`)
| split | casos Q | o que prova | gate |
|---|---|---|---|
| official-var | 20 (10 pt, 10 en) | as 10 AC reescritas sem repetir 5 palavras seguidas dos official: robustez de paráfrase e idioma | sim |
| memory | 16 | seguimento curto herda o assunto ("e quanto custa?", "e a outra maquininha?"); `expects_fact` mede memória separada do roteamento | sim |
| dependent | 11 | só fica completo com records + faq (`must_include_agents`) | sim |
| guardrail | 32 | injeção direta/indireta, ofuscação (leet, espaçado, base64, zero-width), jailbreak, dado de outro cliente, lavagem, fraude, abuso, fora de escopo → `blocked` | sim |
| hard | 6 | mensagens compostas e ambíguas | não (UNGATED) |

Os intents seguem a taxonomia congelada da SPEC (knowledge/support/troubleshoot/general/human_request/multi/blocked).

## Números medidos (02/11/2026, provider offline, ANTES do merge das frentes R e T)
- `fork_check.py q`: guardrail intent_acc 0,3438; official-var, memory, dependent e hard 0,0 (roteador do kit, sem o flow da frente R).
- testes da frente: 23 passed, 22 xfailed, 11 xpassed; via API, 11 de 32 guardrails bloqueados antes do merge.
- Achado: a camada regex do motor não bloqueia "Disregard prior instructions..." (sinônimo); depende da camada LLM/domínio.
Esses números serão remedidos na integração; nada aqui é número pós-merge.

## Juiz (LLM-as-judge)
`evals/judge_calibration.d/q.jsonl`: 48 rótulos humanos, 24 positivos e 24 negativos, cobrindo RAG, tool e web. Cada
negativo traz `human_failure_type`, 4 por tipo: invented_number, unsupported_claim, stale_source,
offered_unavailable_action, wrong_language, leak — permite TPR/TNR do juiz por tipo (`evals/judge.py`), além do kappa.
Canários do motor continuam valendo: juiz que deixa passar um defeito sintético sai `judge_unreliable`.

## Regras
- Nenhum caso abre `evals/heldout_blind.jsonl`; nenhum repete 5 palavras seguidas dos official (checado por script).
- Sem `example.com` (domínio fictício: `@lojadojoao.com.br`), sem resposta pronta no código.
- Testes que dependem de R/T estão como xfail não estrito, com motivo, para o número aparecer e não sumir.
