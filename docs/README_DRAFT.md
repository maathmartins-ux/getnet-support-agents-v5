# Rascunho do README — §5 e §7 (para colar; números entre {{ }} saem do placar/fill_readme)

## §5 Perguntas da entrevista, respondidas (linhas da tabela)

| Pergunta | Resposta curta | Onde está a prova |
|---|---|---|
| Quais respostas oficiais o juiz reprova, e por quê, se intenção e ferramentas acertam? | Na rodada 1, 4 das 10 oficiais (official-01, 04, 06, 09, todas em inglês) foram ao humano com intenção e ferramenta certas: o portão "sem fonte" recusava a pergunta (`faq_no_source`), porque com o denso o cosseno das perguntas com e sem fonte ficava na mesma faixa (0,82–0,88). Causa corrigida recalibrando o piso de cosseno do portão 0,88 → 0,82 (prova offline no commit `5d7cee5`); pass^3 do official {{PASS3_R1}} → {{PASS3_R2}}; fundamentadas pelo juiz {{GROUNDED_R1}} → {{GROUNDED_R2}}. | `docs/JUDGE_DIFF.md` |
| O rerank tem ganho medido? Por que está (ou não) no caminho? | Tem ganho e não está no caminho. Gold de passagens essenciais (38 perguntas com fonte): bm25 0,579 / 0,504; denso e5-large **0,842 / 0,715** (entrega); denso + rerank bge-m3-int8 0,947 / 0,807 (Recall@3 / MRR). O rerank passaria as duas metas, mas o p95 medido no relógio (CPU disputada pelos subagentes) passou do orçamento de 3 s por busca; ficou o denso com o portão recalibrado, e a busca fica abaixo da meta, declarada no §7. | `evals/results/retrieval_compare.json`, `data/retriever.json`, `docs/adr/0008-rerank-com-orcamento-de-3s.md` |
| Onde a memória perde informação? | {{memória × roteamento, do bloco "Memória × roteamento" da rodada 2: pass@1 {{MEM_PASS1}}, perdas só de memória {{MEM_ONLY}}, só de roteamento {{ROUTE_ONLY}}}} | §0 e `docs/RESULTS.md` |
| Quanto do kit foi escrito depois das correções anteriores? | O motor genérico veio do kit (commit de scaffold `5f28b22`), que evoluiu com as correções da v1 (7,1), v2 (8,2) e v4 (8,5); no relógio foram escritas {{LINHAS_RELOGIO}} linhas (domínio, corpus, casos, prompts, docs) contra {{LINHAS_KIT}} do kit. A tabela por pasta e o item-a-item "o que a correção pediu × onde" estão na procedência. | `docs/PROCEDENCIA.md`, `docs/KIT_CHANGELOG.md` |
| Como medir o ganho do replanejamento em perguntas reais? | Ablação `no_needs` (mesmos casos, sem o `needs` do Support): no split `dependent`, dependent-07..10 não completam sem o `needs` ({{DEP_ON}} × {{DEP_NO_NEEDS}} de `completed`); nas 40 perguntas reais de lojistas (Reclame Aqui, com link) a ablação ao vivo está em `ablation_replan_no_needs_live.json` ({{REAL_ON}} × {{REAL_NO_NEEDS}}). | `evals/results/ablation_replan*.json` |

## §7 Limitações e próximos passos (itens)

- **Simulado:** os dados de cliente (vendas, recebimentos, maquininhas de `cliente1988` e `cliente2024`) vêm de um CRM
  fictício em `data/`; as escritas (contestação, antecipação, reinício remoto) gravam nesse CRM depois da confirmação
  do lojista (e do operador, nas de risco alto) — nenhum sistema da Getnet é chamado. Clima e câmbio vêm de APIs
  públicas reais (Open-Meteo, PTAX do Banco Central), com a data da consulta.
- **Busca abaixo da meta:** Recall@3 0,842 (meta 0,85) e MRR 0,715 (meta 0,80) com o denso. O rerank medido leva a
  0,947 / 0,807, mas o p95 por busca no relógio passou de 3 s; próximo passo: medir o rerank em máquina sem carga
  (no ensaio do kit, 1,1–1,25 s) e ligá-lo se couber no orçamento.
- **Outras abaixo da meta, com a causa:** {{para cada linha "abaixo" do placar §0: métrica, valor, causa, próximo passo.
  Candidatos medidos até aqui: p95 da resposta ({{P95}}; sem o rerank); o split `hard` (ataques
  semânticos que só a camada LLM pega: offline o regex bloqueia 11/32, ao vivo {{HARD_LIVE}}); avaliação humana com
  10 situações por pessoa e concordância entre humanos {{KAPPA_HUMANOS}}: a 2ª pessoa marcou 5 de 10 como "idioma
  errado", quase todas em conversas em inglês com resposta em inglês, leitura diferente do critério; rótulos
  publicados como vieram, sem edição}}.
- **Gold de busca com 1 rotulador:** as passagens essenciais do `evals/retrieval.d/k.jsonl` foram marcadas às cegas por
  um rotulador só (o kit pede 2); o número de concordância não existe para este corpus. Próximo passo: 2º rotulador com
  `evals/essential_gold.py`.
- **Fora do relógio / não rodou:** as tags `clock-start` e `clock-end` não puderam ser enviadas ao GitHub (o proxy da
  nuvem derruba push de tag); o relógio está em `docs/TIMESHEET.md`, do commit `5f28b22` ao último commit.
  {{o que mais ficou de fora: ex. replan-10 (intenção em "stock dividends"), q-hard-02, q-guardrail-14/15, se não
  corrigidos}}.
