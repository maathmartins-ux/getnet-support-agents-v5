# Resultados completos

Tudo aqui é gerado por `scripts/fill_readme.py` a partir de `evals/results/` commitado. O resumo com metas está no
§0 do [README](../README.md).

## Offline (gate do CI)

<!-- eval:begin -->
Modo: `in-process` · provedor `offline`

| Métrica | official | replan | dependent | parallel | approval | memory | real | official-var | hard | guardrail | heldout | ALL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cases | 10 | 20 | 21 | 4 | 6 | 32 | 40 | 20 | 27 | 11 | 80 | 271 |
| intent_acc | 100.0 [IC95 72.2–100.0; n=10] | 100.0 [IC95 83.9–100.0; n=20] | 100.0 [IC95 84.5–100.0; n=21] | 100.0 [IC95 51.0–100.0; n=4] | 100.0 [IC95 61.0–100.0; n=6] | 100.0 [IC95 89.3–100.0; n=32] | — | 100.0 [IC95 83.9–100.0; n=20] | 11.1 [IC95 3.9–28.1; n=27] | 100.0 [IC95 74.1–100.0; n=11] | 67.5 [IC95 56.6–76.8; n=80] | 78.4 [IC95 72.6–83.2; n=231] |
| handoff_acc | 100.0 [IC95 72.2–100.0; n=10] | 35.0 [IC95 18.1–56.7; n=20] | 100.0 [IC95 84.5–100.0; n=21] | 75.0 [IC95 30.1–95.4; n=4] | 100.0 [IC95 61.0–100.0; n=6] | 93.8 [IC95 79.9–98.3; n=32] | — | 100.0 [IC95 83.9–100.0; n=20] | 55.6 [IC95 37.3–72.4; n=27] | 100.0 [IC95 74.1–100.0; n=11] | 85.0 [IC95 75.6–91.2; n=80] | 82.7 [IC95 77.3–87.0; n=231] |
| handoff_outcome_acc | 100.0 [IC95 72.2–100.0; n=10] | 35.0 [IC95 18.1–56.7; n=20] | 100.0 [IC95 84.5–100.0; n=21] | 75.0 [IC95 30.1–95.4; n=4] | 100.0 [IC95 61.0–100.0; n=6] | 93.8 [IC95 79.9–98.3; n=32] | — | 100.0 [IC95 83.9–100.0; n=20] | 55.6 [IC95 37.3–72.4; n=27] | 100.0 [IC95 74.1–100.0; n=11] | 85.0 [IC95 75.6–91.2; n=80] | 82.7 [IC95 77.3–87.0; n=231] |
| blocked_acc | — | — | — | — | — | — | — | — | — | — | — | — |
| language_acc | 40.0 [IC95 16.8–68.7; n=10] | 80.0 [IC95 58.4–91.9; n=20] | 57.1 [IC95 36.5–75.5; n=21] | 75.0 [IC95 30.1–95.4; n=4] | 100.0 [IC95 61.0–100.0; n=6] | 78.1 [IC95 61.2–89.0; n=32] | 100.0 [IC95 87.9–100.0; n=28] | 68.4 [IC95 46.0–84.6; n=19] | 87.5 [IC95 69.0–95.7; n=24] | 100.0 [IC95 74.1–100.0; n=11] | 84.5 [IC95 74.3–91.1; n=71] | 80.9 [IC95 75.5–85.3; n=246] |
| tools_acc | 100.0 [IC95 43.9–100.0; n=3] | — | 100.0 [IC95 84.5–100.0; n=21] | — | 100.0 [IC95 61.0–100.0; n=6] | 95.7 [IC95 79.0–99.2; n=23] | — | 83.3 [IC95 43.6–97.0; n=6] | 20.0 [IC95 3.6–62.4; n=5] | — | 72.5 [IC95 57.2–83.9; n=40] | 83.7 [IC95 75.4–89.5; n=104] |
| pending_action_acc | — | — | — | — | 100.0 [IC95 61.0–100.0; n=6] | — | — | — | — | — | — | 100.0 [IC95 61.0–100.0; n=6] |
| replanned_acc | — | 50.0 [IC95 29.9–70.1; n=20] | — | — | — | — | — | — | — | — | — | 50.0 [IC95 29.9–70.1; n=20] |
| completed_acc | 100.0 [IC95 20.7–100.0; n=1] | — | 100.0 [IC95 84.5–100.0; n=21] | — | — | — | — | 100.0 [IC95 34.2–100.0; n=2] | — | — | — | 100.0 [IC95 86.2–100.0; n=24] |
| no_leak_acc | — | — | — | — | — | — | — | — | — | — | — | — |
| numbers_acc | 100.0 [IC95 72.2–100.0; n=10] | 100.0 [IC95 83.9–100.0; n=20] | 100.0 [IC95 84.5–100.0; n=21] | 100.0 [IC95 51.0–100.0; n=4] | 100.0 [IC95 61.0–100.0; n=6] | 100.0 [IC95 89.3–100.0; n=32] | 100.0 [IC95 91.2–100.0; n=40] | 100.0 [IC95 83.9–100.0; n=20] | 100.0 [IC95 87.5–100.0; n=27] | — | 100.0 [IC95 95.2–100.0; n=77] | 100.0 [IC95 98.5–100.0; n=257] |
| memory_acc | — | — | — | — | — | 76.7 [IC95 59.1–88.2; n=30] | — | — | — | — | — | 76.7 [IC95 59.1–88.2; n=30] |
| claims_acc | 100.0 [IC95 72.2–100.0; n=10] | 100.0 [IC95 83.9–100.0; n=20] | 100.0 [IC95 84.5–100.0; n=21] | 100.0 [IC95 51.0–100.0; n=4] | 100.0 [IC95 61.0–100.0; n=6] | 96.9 [IC95 84.3–99.4; n=32] | 100.0 [IC95 91.2–100.0; n=40] | 100.0 [IC95 83.9–100.0; n=20] | 100.0 [IC95 87.5–100.0; n=27] | — | 100.0 [IC95 95.2–100.0; n=77] | 99.6 [IC95 97.8–99.9; n=257] |
| language_undetected | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 1 | 3 | 0 | 9 | 25 |
| recall@3 | — | — | — | — | — | — | — | — | — | — | — | — |
| mrr | — | — | — | — | — | — | — | — | — | — | — | — |
| p50_ms | 62.8 | 49.4 | 52.7 | 65.0 | 46.2 | 97.0 | 50.6 | 56.2 | 49.0 | 5.6 | 48.3 | 50.6 |
| p95_ms | 1647.3 | 67.4 | 64.5 | 67.1 | 50.6 | 122.8 | 138.7 | 1603.8 | 62.6 | 8.0 | 666.9 | 138.7 |
| cost_usd | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| crashes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Gate (splits approval, dependent, guardrail, memory, official, official-var, parallel, replan): intent 100.0% [IC95 97.0–100.0; n=124] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Memória × roteamento:
- split `memory` (n=32): **memória** 78.1% (fatos esperados 76.7% (n=30); números 100.0% (n=32)) · **roteamento** 90.6% · pass@1 59.4% · perdas só de roteamento: — · só de memória: memory-06, memory-15, q-memory-11, q-memory-13 · nas duas: memory-07, q-memory-07, q-memory-14

Falhas por checagem × split: claims memory 1 · handoff hard 12, heldout 12, memory 2, parallel 1, replan 13 · handoff_outcome hard 12, heldout 12, memory 2, parallel 1, replan 13 · intent hard 24, heldout 26 · language dependent 9, hard 3, heldout 11, memory 7, official 6, official-var 6, parallel 1, replan 4 · memory memory 7 · replanned replan 10 · tools hard 4, heldout 11, memory 1, official-var 1
Confusão de intenção (esperada → obtida): blocked → knowledge 19, support 4, multi 1 · general → knowledge 2, support 1 · human_request → knowledge 1 · knowledge → support 3 · multi → support 9, knowledge 1 · support → knowledge 1, troubleshoot 1, general 1 · troubleshoot → support 5, knowledge 1

Matriz de confusão do router (todos os splits):

| esperada \ obtida | blocked | general | human_request | knowledge | multi | support | troubleshoot | acerto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| blocked | **14** | · | · | 19 | 1 | 4 | · | 37% |
| general | · | **11** | · | 2 | · | 1 | · | 79% |
| human_request | · | · | **9** | 1 | · | · | · | 90% |
| knowledge | · | · | · | **50** | · | 3 | · | 94% |
| multi | · | · | · | 1 | **7** | 9 | · | 41% |
| support | · | 1 | · | 1 | · | **48** | 1 | 94% |
| troubleshoot | · | · | · | 1 | · | 5 | **42** | 88% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921
<!-- eval:end -->

## Ao vivo (LLM real, por split)

<!-- eval-live:begin -->
### Split `approval` — `live_approval.json`

Provedor `anthropic` · status `complete` · gasto US$ 0.27375 (teto 0.872727)

| Métrica | approval | ALL |
|---|---:|---:|
| cases | 18 | 18 |
| intent_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| handoff_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| handoff_outcome_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| tools_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| pending_action_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| replanned_acc | — | — |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 82.4–100.0; n=18] | 100.0 [IC95 82.4–100.0; n=18] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 6157.5 | 6157.5 |
| p95_ms | 11655.0 | 11655.0 |
| cost_usd | 0.27375 | 0.27375 |
| crashes | 0 | 0 |

Gate (splits approval): intent 100.0% [IC95 82.4–100.0; n=18] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Matriz de confusão do router (todos os splits):

| esperada \ obtida | support | acerto |
|---|---:|---:|
| support | **18** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 100.0% [IC95 82.4–100.0; n=18] · pass^3 100.0% [IC95 61.0–100.0; n=6] · instáveis: —

Ao vivo: status `complete` · gasto US$ 0.27375 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `dependent` — `live_dependent.json`

Provedor `anthropic` · status `aborted_max_usd` · gasto US$ 0.86623 (teto 0.872727)

| Métrica | dependent | ALL |
|---|---:|---:|
| cases | 22 | 22 |
| intent_acc | 100.0 [IC95 85.1–100.0; n=22] | 100.0 [IC95 85.1–100.0; n=22] |
| handoff_acc | 50.0 [IC95 30.7–69.3; n=22] | 50.0 [IC95 30.7–69.3; n=22] |
| handoff_outcome_acc | 50.0 [IC95 30.7–69.3; n=22] | 50.0 [IC95 30.7–69.3; n=22] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 85.1–100.0; n=22] | 100.0 [IC95 85.1–100.0; n=22] |
| tools_acc | 100.0 [IC95 85.1–100.0; n=22] | 100.0 [IC95 85.1–100.0; n=22] |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | 100.0 [IC95 85.1–100.0; n=22] | 100.0 [IC95 85.1–100.0; n=22] |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 85.1–100.0; n=22] | 100.0 [IC95 85.1–100.0; n=22] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 85.1–100.0; n=22] | 100.0 [IC95 85.1–100.0; n=22] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 13173.9 | 13173.9 |
| p95_ms | 26235.6 | 26235.6 |
| cost_usd | 0.86623 | 0.86623 |
| crashes | 0 | 0 |

Gate (splits dependent): intent 100.0% [IC95 85.1–100.0; n=22] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Falhas por checagem × split: handoff dependent 11 · handoff_outcome dependent 11

Matriz de confusão do router (todos os splits):

| esperada \ obtida | troubleshoot | acerto |
|---|---:|---:|
| troubleshoot | **22** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 50.0% [IC95 30.7–69.3; n=22] · pass^3 52.4% [IC95 32.4–71.7; n=21] · instáveis: —

Ao vivo: status `aborted_max_usd` · gasto US$ 0.86623 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `guardrail` — `live_guardrail.json`

Provedor `anthropic` · status `complete` · gasto US$ 0.0 (teto 0.872727)

| Métrica | guardrail | ALL |
|---|---:|---:|
| cases | 33 | 33 |
| intent_acc | 100.0 [IC95 89.6–100.0; n=33] | 100.0 [IC95 89.6–100.0; n=33] |
| handoff_acc | 100.0 [IC95 89.6–100.0; n=33] | 100.0 [IC95 89.6–100.0; n=33] |
| handoff_outcome_acc | 100.0 [IC95 89.6–100.0; n=33] | 100.0 [IC95 89.6–100.0; n=33] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 89.6–100.0; n=33] | 100.0 [IC95 89.6–100.0; n=33] |
| tools_acc | — | — |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | — | — |
| memory_acc | — | — |
| claims_acc | — | — |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 15.0 | 15.0 |
| p95_ms | 912.9 | 912.9 |
| cost_usd | 0.0 | 0.0 |
| crashes | 0 | 0 |

Gate (splits guardrail): intent 100.0% [IC95 89.6–100.0; n=33] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Matriz de confusão do router (todos os splits):

| esperada \ obtida | blocked | acerto |
|---|---:|---:|
| blocked | **33** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 100.0% [IC95 89.6–100.0; n=33] · pass^3 100.0% [IC95 74.1–100.0; n=11] · instáveis: —

Ao vivo: status `complete` · gasto US$ 0.0 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `hard` — `live_hard.json`

Provedor `anthropic` · status `complete` · gasto US$ 0.472716 (teto 0.872727)

| Métrica | hard | ALL |
|---|---:|---:|
| cases | 81 | 81 |
| intent_acc | 96.3 [IC95 89.7–98.7; n=81] | 96.3 [IC95 89.7–98.7; n=81] |
| handoff_acc | 91.4 [IC95 83.2–95.8; n=81] | 91.4 [IC95 83.2–95.8; n=81] |
| handoff_outcome_acc | 91.4 [IC95 83.2–95.8; n=81] | 91.4 [IC95 83.2–95.8; n=81] |
| blocked_acc | — | — |
| language_acc | 96.3 [IC95 89.7–98.7; n=81] | 96.3 [IC95 89.7–98.7; n=81] |
| tools_acc | 100.0 [IC95 79.6–100.0; n=15] | 100.0 [IC95 79.6–100.0; n=15] |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 84.5–100.0; n=21] | 100.0 [IC95 84.5–100.0; n=21] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 84.5–100.0; n=21] | 100.0 [IC95 84.5–100.0; n=21] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 2014.7 | 2014.7 |
| p95_ms | 13532.5 | 13532.5 |
| cost_usd | 0.472716 | 0.472716 |
| crashes | 0 | 0 |

Gate (splits ): intent 0.0% [n=0] (mínimo 90%) → **FAIL**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Falhas por checagem × split: handoff hard 7 · handoff_outcome hard 7 · intent hard 3 · language hard 3
Confusão de intenção (esperada → obtida): blocked → knowledge 3

Matriz de confusão do router (todos os splits):

| esperada \ obtida | blocked | human_request | knowledge | multi | support | troubleshoot | acerto |
|---|---:|---:|---:|---:|---:|---:|---:|
| blocked | **60** | · | 3 | · | · | · | 95% |
| human_request | · | **3** | · | · | · | · | 100% |
| multi | · | · | · | **6** | · | · | 100% |
| support | · | · | · | · | **6** | · | 100% |
| troubleshoot | · | · | · | · | · | **3** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 87.6% [IC95 78.7–93.2; n=81] · pass^3 85.2% [IC95 67.5–94.1; n=27] · instáveis: q-hard-05

Ao vivo: status `complete` · gasto US$ 0.472716 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `heldout` — `live_heldout.json`

Provedor `anthropic` · status `aborted_max_usd` · gasto US$ 0.899902 (teto 0.872727)

| Métrica | heldout | ALL |
|---|---:|---:|
| cases | 54 | 54 |
| intent_acc | 100.0 [IC95 93.4–100.0; n=54] | 100.0 [IC95 93.4–100.0; n=54] |
| handoff_acc | 72.2 [IC95 59.1–82.4; n=54] | 72.2 [IC95 59.1–82.4; n=54] |
| handoff_outcome_acc | 72.2 [IC95 59.1–82.4; n=54] | 72.2 [IC95 59.1–82.4; n=54] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 93.2–100.0; n=53] | 100.0 [IC95 93.2–100.0; n=53] |
| tools_acc | 96.3 [IC95 81.7–99.3; n=27] | 96.3 [IC95 81.7–99.3; n=27] |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 93.0–100.0; n=51] | 100.0 [IC95 93.0–100.0; n=51] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 93.0–100.0; n=51] | 100.0 [IC95 93.0–100.0; n=51] |
| language_undetected | 1 | 1 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 7024.0 | 7024.0 |
| p95_ms | 15612.4 | 15612.4 |
| cost_usd | 0.899902 | 0.899902 |
| crashes | 0 | 0 |

Gate (splits ): intent 0.0% [n=0] (mínimo 90%) → **FAIL**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Falhas por checagem × split: handoff heldout 15 · handoff_outcome heldout 15 · tools heldout 1

Matriz de confusão do router (todos os splits):

| esperada \ obtida | blocked | general | human_request | knowledge | multi | support | troubleshoot | acerto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| blocked | **3** | · | · | · | · | · | · | 100% |
| general | · | **6** | · | · | · | · | · | 100% |
| human_request | · | · | **6** | · | · | · | · | 100% |
| knowledge | · | · | · | **12** | · | · | · | 100% |
| multi | · | · | · | · | **3** | · | · | 100% |
| support | · | · | · | · | · | **16** | · | 100% |
| troubleshoot | · | · | · | · | · | · | **8** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 72.2% [IC95 59.1–82.4; n=54] · pass^3 72.2% [IC95 59.1–82.4; n=54] · instáveis: —

Ao vivo: status `aborted_max_usd` · gasto US$ 0.899902 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `memory` — `live_memory.json`

Provedor `anthropic` · status `aborted_max_usd` · gasto US$ 0.899672 (teto 0.872727)

| Métrica | memory | ALL |
|---|---:|---:|
| cases | 49 | 49 |
| intent_acc | 91.8 [IC95 80.8–96.8; n=49] | 91.8 [IC95 80.8–96.8; n=49] |
| handoff_acc | 71.4 [IC95 57.6–82.2; n=49] | 71.4 [IC95 57.6–82.2; n=49] |
| handoff_outcome_acc | 71.4 [IC95 57.6–82.2; n=49] | 71.4 [IC95 57.6–82.2; n=49] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 92.7–100.0; n=49] | 100.0 [IC95 92.7–100.0; n=49] |
| tools_acc | 88.9 [IC95 74.7–95.6; n=36] | 88.9 [IC95 74.7–95.6; n=36] |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 92.7–100.0; n=49] | 100.0 [IC95 92.7–100.0; n=49] |
| memory_acc | 86.7 [IC95 73.8–93.7; n=45] | 86.7 [IC95 73.8–93.7; n=45] |
| claims_acc | 100.0 [IC95 92.7–100.0; n=49] | 100.0 [IC95 92.7–100.0; n=49] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 13315.2 | 13315.2 |
| p95_ms | 29396.4 | 29396.4 |
| cost_usd | 0.899672 | 0.899672 |
| crashes | 0 | 0 |

Gate (splits memory): intent 91.8% [IC95 80.8–96.8; n=49] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Memória × roteamento:
- split `memory` (n=49): **memória** 87.8% (fatos esperados 86.7% (n=45); números 100.0% (n=49)) · **roteamento** 71.4% · pass@1 65.3% · perdas só de roteamento: memory-03, memory-09, memory-12, memory-16, q-memory-08, q-memory-09, q-memory-15, memory-03, memory-09, memory-12, memory-16 · só de memória: q-memory-10, memory-05, memory-14 · nas duas: memory-07, q-memory-07, memory-07

Falhas por checagem × split: handoff memory 14 · handoff_outcome memory 14 · intent memory 4 · memory memory 6 · tools memory 4
Confusão de intenção (esperada → obtida): support → knowledge 2 · troubleshoot → support 2

Matriz de confusão do router (todos os splits):

| esperada \ obtida | knowledge | support | troubleshoot | acerto |
|---|---:|---:|---:|---:|
| knowledge | **13** | · | · | 100% |
| support | 2 | **22** | · | 92% |
| troubleshoot | · | 2 | **10** | 83% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 65.3% [IC95 51.3–77.1; n=49] · pass^3 62.5% [IC95 45.3–77.1; n=32] · instáveis: memory-05, memory-14

Ao vivo: status `aborted_max_usd` · gasto US$ 0.899672 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `official-var` — `live_official-var.json`

Provedor `anthropic` · status `aborted_max_usd` · gasto US$ 0.887625 (teto 0.872727)

| Métrica | official-var | ALL |
|---|---:|---:|
| cases | 55 | 55 |
| intent_acc | 100.0 [IC95 93.5–100.0; n=55] | 100.0 [IC95 93.5–100.0; n=55] |
| handoff_acc | 69.1 [IC95 56.0–79.7; n=55] | 69.1 [IC95 56.0–79.7; n=55] |
| handoff_outcome_acc | 69.1 [IC95 56.0–79.7; n=55] | 69.1 [IC95 56.0–79.7; n=55] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 93.5–100.0; n=55] | 100.0 [IC95 93.5–100.0; n=55] |
| tools_acc | 100.0 [IC95 81.6–100.0; n=17] | 100.0 [IC95 81.6–100.0; n=17] |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | 100.0 [IC95 61.0–100.0; n=6] | 100.0 [IC95 61.0–100.0; n=6] |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 93.5–100.0; n=55] | 100.0 [IC95 93.5–100.0; n=55] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 93.5–100.0; n=55] | 100.0 [IC95 93.5–100.0; n=55] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 4942.0 | 4942.0 |
| p95_ms | 20871.0 | 20871.0 |
| cost_usd | 0.887625 | 0.887625 |
| crashes | 0 | 0 |

Gate (splits official-var): intent 100.0% [IC95 93.5–100.0; n=55] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Falhas por checagem × split: handoff official-var 17 · handoff_outcome official-var 17

Matriz de confusão do router (todos os splits):

| esperada \ obtida | general | knowledge | support | troubleshoot | acerto |
|---|---:|---:|---:|---:|---:|
| general | **11** | · | · | · | 100% |
| knowledge | · | **27** | · | · | 100% |
| support | · | · | **6** | · | 100% |
| troubleshoot | · | · | · | **11** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 69.1% [IC95 56.0–79.7; n=55] · pass^3 65.0% [IC95 43.3–81.9; n=20] · instáveis: q-official-var-04

Ao vivo: status `aborted_max_usd` · gasto US$ 0.887625 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `official` — `live_official.json`

Provedor `anthropic` · status `complete` · gasto US$ 0.529784 (teto 2.0)

| Métrica | official | ALL |
|---|---:|---:|
| cases | 30 | 30 |
| intent_acc | 100.0 [IC95 88.6–100.0; n=30] | 100.0 [IC95 88.6–100.0; n=30] |
| handoff_acc | 70.0 [IC95 52.1–83.3; n=30] | 70.0 [IC95 52.1–83.3; n=30] |
| handoff_outcome_acc | 70.0 [IC95 52.1–83.3; n=30] | 70.0 [IC95 52.1–83.3; n=30] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 88.6–100.0; n=30] | 100.0 [IC95 88.6–100.0; n=30] |
| tools_acc | 100.0 [IC95 70.1–100.0; n=9] | 100.0 [IC95 70.1–100.0; n=9] |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | 100.0 [IC95 43.9–100.0; n=3] | 100.0 [IC95 43.9–100.0; n=3] |
| no_leak_acc | — | — |
| numbers_acc | 96.7 [IC95 83.3–99.4; n=30] | 96.7 [IC95 83.3–99.4; n=30] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 88.6–100.0; n=30] | 100.0 [IC95 88.6–100.0; n=30] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 5080.7 | 5080.7 |
| p95_ms | 18849.9 | 18849.9 |
| cost_usd | 0.529784 | 0.529784 |
| crashes | 0 | 0 |

Gate (splits official): intent 100.0% [IC95 88.6–100.0; n=30] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Falhas por checagem × split: handoff official 9 · handoff_outcome official 9 · numbers official 1

Matriz de confusão do router (todos os splits):

| esperada \ obtida | general | knowledge | support | troubleshoot | acerto |
|---|---:|---:|---:|---:|---:|
| general | **6** | · | · | · | 100% |
| knowledge | · | **15** | · | · | 100% |
| support | · | · | **3** | · | 100% |
| troubleshoot | · | · | · | **6** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 66.7% [IC95 48.8–80.8; n=30] · pass^3 60.0% [IC95 31.3–83.2; n=10] · instáveis: official-02

Ao vivo: status `complete` · gasto US$ 0.529784 (teto 2.0) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `parallel` — `live_parallel.json`

Provedor `anthropic` · status `complete` · gasto US$ 0.426532 (teto 2.0)

| Métrica | parallel | ALL |
|---|---:|---:|
| cases | 12 | 12 |
| intent_acc | 100.0 [IC95 75.8–100.0; n=12] | 100.0 [IC95 75.8–100.0; n=12] |
| handoff_acc | 75.0 [IC95 46.8–91.1; n=12] | 75.0 [IC95 46.8–91.1; n=12] |
| handoff_outcome_acc | 75.0 [IC95 46.8–91.1; n=12] | 75.0 [IC95 46.8–91.1; n=12] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 75.8–100.0; n=12] | 100.0 [IC95 75.8–100.0; n=12] |
| tools_acc | — | — |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 75.8–100.0; n=12] | 100.0 [IC95 75.8–100.0; n=12] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 75.8–100.0; n=12] | 100.0 [IC95 75.8–100.0; n=12] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 11617.6 | 11617.6 |
| p95_ms | 14139.4 | 14139.4 |
| cost_usd | 0.426532 | 0.426532 |
| crashes | 0 | 0 |

Gate (splits parallel): intent 100.0% [IC95 75.8–100.0; n=12] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Falhas por checagem × split: handoff parallel 3 · handoff_outcome parallel 3

Matriz de confusão do router (todos os splits):

| esperada \ obtida | multi | acerto |
|---|---:|---:|
| multi | **12** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 75.0% [IC95 46.8–91.1; n=12] · pass^3 75.0% [IC95 30.1–95.4; n=4] · instáveis: —

Ao vivo: status `complete` · gasto US$ 0.426532 (teto 2.0) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `real` — `live_real.json`

Provedor `anthropic` · status `aborted_max_usd` · gasto US$ 0.865634 (teto 0.872727)

| Métrica | real | ALL |
|---|---:|---:|
| cases | 33 | 33 |
| intent_acc | — | — |
| handoff_acc | — | — |
| handoff_outcome_acc | — | — |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 89.6–100.0; n=33] | 100.0 [IC95 89.6–100.0; n=33] |
| tools_acc | — | — |
| pending_action_acc | — | — |
| replanned_acc | — | — |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 89.6–100.0; n=33] | 100.0 [IC95 89.6–100.0; n=33] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 89.6–100.0; n=33] | 100.0 [IC95 89.6–100.0; n=33] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 12360.3 | 12360.3 |
| p95_ms | 18676.1 | 18676.1 |
| cost_usd | 0.865634 | 0.865634 |
| crashes | 0 | 0 |

Gate (splits ): intent 0.0% [n=0] (mínimo 90%) → **FAIL**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 100.0% [IC95 89.6–100.0; n=33] · pass^3 100.0% [IC95 89.6–100.0; n=33] · instáveis: —

Ao vivo: status `aborted_max_usd` · gasto US$ 0.865634 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921

### Split `replan` — `live_replan.json`

Provedor `anthropic` · status `complete` · gasto US$ 0.58755 (teto 0.872727)

| Métrica | replan | ALL |
|---|---:|---:|
| cases | 60 | 60 |
| intent_acc | 95.0 [IC95 86.3–98.3; n=60] | 95.0 [IC95 86.3–98.3; n=60] |
| handoff_acc | 83.3 [IC95 72.0–90.7; n=60] | 83.3 [IC95 72.0–90.7; n=60] |
| handoff_outcome_acc | 83.3 [IC95 72.0–90.7; n=60] | 83.3 [IC95 72.0–90.7; n=60] |
| blocked_acc | — | — |
| language_acc | 100.0 [IC95 94.0–100.0; n=60] | 100.0 [IC95 94.0–100.0; n=60] |
| tools_acc | — | — |
| pending_action_acc | — | — |
| replanned_acc | 83.3 [IC95 72.0–90.7; n=60] | 83.3 [IC95 72.0–90.7; n=60] |
| completed_acc | — | — |
| no_leak_acc | — | — |
| numbers_acc | 100.0 [IC95 94.0–100.0; n=60] | 100.0 [IC95 94.0–100.0; n=60] |
| memory_acc | — | — |
| claims_acc | 100.0 [IC95 94.0–100.0; n=60] | 100.0 [IC95 94.0–100.0; n=60] |
| language_undetected | 0 | 0 |
| recall@3 | — | — |
| mrr | — | — |
| p50_ms | 3795.6 | 3795.6 |
| p95_ms | 22648.8 | 22648.8 |
| cost_usd | 0.58755 | 0.58755 |
| crashes | 0 | 0 |

Gate (splits replan): intent 95.0% [IC95 86.3–98.3; n=60] (mínimo 90%) → **PASS**. Medidos fora do gate: hard, heldout, real. Isolamento: `db_per_case`.

Falhas por checagem × split: handoff replan 10 · handoff_outcome replan 10 · intent replan 3 · replanned replan 10
Confusão de intenção (esperada → obtida): knowledge → general 3

Matriz de confusão do router (todos os splits):

| esperada \ obtida | general | knowledge | support | acerto |
|---|---:|---:|---:|---:|
| knowledge | 3 | **33** | · | 92% |
| support | · | · | **24** | 100% |

Portão sem fonte: limiar efetivo 12.433 (MIN_SCORE) → responde 15.8% [IC95 7.4–30.4; n=38] dos com fonte, recusa 94.1% [IC95 73.0–99.0; n=17] dos sem fonte · recomendado 12.433 → responde 15.8% [IC95 7.4–30.4; n=38], recusa 94.1% [IC95 73.0–99.0; n=17] (38 com fonte, 17 sem; 1 sem fonte fora da conta por não chegarem ao agente de conhecimento; critério: max pos_answered com neg_refused >= 0.85; empate → menor limiar)

Estabilidade (3 rodadas): pass@1 83.3% [IC95 72.0–90.7; n=60] · pass^3 80.0% [IC95 58.4–91.9; n=20] · instáveis: replan-16

Ao vivo: status `complete` · gasto US$ 0.58755 (teto 0.872727) · erros de LLM 0

Retrieval ativo (dense, `evals/retrieval.jsonl`): Recall@3 **0.842** · MRR **0.715** · hit@3 0.842 [IC95 69.6–92.6; n=38] (38 perguntas); por página: Recall@3 **0.726** · MRR **0.86** · hit@3 0.921
<!-- eval-live:end -->

## Juiz LLM sobre as respostas ao vivo

<!-- judge:begin -->
Modelo `claude-opus-5-5` · status `ran` · arquivos live_official.json, live_replan.json · gasto US$ 1.432508

| split | casos | grounded | helpful | nota média |
|---|---:|---:|---:|---:|
| official | 30 | 1.0 [IC95 88.6–100.0; n=30] | 0.733 [IC95 55.6–85.8; n=30] | 4.27 |
| replan | 60 | 0.983 [IC95 91.1–99.7; n=60] | 1.0 [IC95 94.0–100.0; n=60] | 4.3 |
| ALL | 90 | 0.989 [IC95 94.0–99.8; n=90] | 0.911 [IC95 83.4–95.4; n=90] | 4.29 |

Calibração humana: 48 rótulos · concordância **0.792** [IC95 65.7–88.3; n=48] · kappa de Cohen **0.583** · TPR 0.875 [IC95 69.0–95.7; n=24] (24 grounded) · TNR 0.708 [IC95 50.8–85.1; n=24] (24 não grounded) · discordâncias: q-cal-09, q-cal-10, q-cal-14, q-cal-33, q-cal-34, q-cal-35, q-cal-36, q-cal-41, q-cal-43, q-cal-44
- rag: concordância 0.875 [IC95 64.0–96.5; n=16] · kappa 0.738 (16 rótulos)
- tool: concordância 0.85 [IC95 64.0–94.8; n=20] · kappa 0.687 (20 rótulos)
- web: concordância 0.583 [IC95 32.0–80.7; n=12] · kappa 0.167 (12 rótulos)

Canários: o juiz reprovou **4/4** registros sintéticos com defeito conhecido (contradiz a evidência, afirma sem evidência, idioma errado, vaza dado de outro cliente).
Família: juiz `claude-opus-5-5` (anthropic) × gerador `claude-haiku-5-5`, `claude-sonnet-5-5` (anthropic): **mesma família**. juiz da mesma família do gerador (anthropic): pode favorecer texto da própria família; para outra família, JUDGE_PROVIDER=openai_compat + JUDGE_BASE_URL/JUDGE_MODEL/JUDGE_API_KEY
<!-- judge:end -->

## Validação humana (às cegas, por rotulador)

<!-- human:begin -->
10 respostas ao vivo rotuladas às cegas pelo dono: humano aprova 2/10, checagem automática aprova 7/10; concordância **0.3**, kappa **-0.129**.
- rotulador `bianca`: 10 rótulos · humano × automático: concordância 0.3, kappa -0.129
- rotulador `matheus`: 10 rótulos · humano × automático: concordância 0.8, kappa 0.412
Entre humanos (bianca × matheus, 10 respostas em comum): concordância **0.3**, kappa **0.054**; divergem: memory-05, memory-13, official-04, official-05, official-10, q-memory-05, q-memory-16.
Aviso: só 10 rótulos: abaixo de 20 não dá para confiar.
- `official-05`: humano fail × automático pass wrong_language
- `memory-13`: humano fail × automático pass wrong_route
- `official-10`: humano fail × automático pass wrong_language
- `q-memory-16`: humano fail × automático pass wrong_language
- `q-memory-05`: humano fail × automático pass wrong_language
- `q-memory-15`: humano pass × automático fail
- `memory-05`: humano fail × automático pass wrong_language
<!-- human:end -->

## Busca (sem LLM; escolha medida em `data/retriever.json`)

<!-- retrieval:begin -->
Gold `retrieval.jsonl`, medido em 2026-11-02T18:44:01+00:00 (commit `c081632`), CPU, sem LLM. Critério: maior MRR com p95 <= 3000 ms e RAM <= 4096 MB (empate: Recall@3, depois p95); orçamento p95 3000 ms.

| configuração | Recall@3 | MRR | hit@3 | nDCG@3 | URL hit@3 | p50 ms | p95 ms | RAM MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bm25 | 0.579 | 0.504 | 0.579 | 0.523 | 0.763 | 0.8 | 1.3 | 40.1 |
| hybrid | 0.789 | 0.653 | 0.789 | 0.689 | 0.842 | 83.3 | 119.9 | 1541.3 |
| dense **← escolhida** | 0.842 | 0.715 | 0.842 | 0.748 | 0.921 | 81.0 | 120.1 | 1541.3 |
| bm25+cross | 0.684 | 0.671 | 0.684 | 0.674 | 0.842 | 2405.0 | 3531.3 | 874.8 |
| hybrid+cross | 0.895 | 0.811 | 0.895 | 0.833 | 0.947 | 2521.1 | 3125.9 | 2376.0 |
| dense+cross | 0.895 | 0.794 | 0.895 | 0.82 | 0.974 | 2551.7 | 3483.6 | 2376.0 |
<!-- retrieval:end -->

## Replanejamento (com × sem)

<!-- replan:begin -->
| fonte | casos | replanned_acc | handoff_acc | handoff_outcome_acc | intent_acc |
|---|---:|---:|---:|---:|---:|
| offline | 20 | 50.0 [IC95 29.9–70.1; n=20] | 35.0 [IC95 18.1–56.7; n=20] | 35.0 [IC95 18.1–56.7; n=20] | 100.0 [IC95 83.9–100.0; n=20] |
| ao vivo (live_replan.json) | 60 | 83.3 [IC95 72.0–90.7; n=60] | 83.3 [IC95 72.0–90.7; n=60] | 83.3 [IC95 72.0–90.7; n=60] | 95.0 [IC95 86.3–98.3; n=60] |

- `replan-02` (offline): faq:no_source->escalation
- `replan-08` (offline): faq:no_source->escalation
- `replan-10` (offline): faq:no_source->escalation
- `replan-13` (offline): records:need->escalation (registro citado pelo cliente não existe na conta)
- `replan-14` (offline): records:need->escalation (registro citado pelo cliente não existe na conta)
<!-- replan:end -->
