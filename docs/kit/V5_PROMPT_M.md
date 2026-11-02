# Prompt da sessão principal da V5 — pronto para colar (kit v5.1.0, 58 min)

Antes: [PLAYBOOK.md](PLAYBOOK.md) §0 inteiro, em especial **A6/A8 (limite da API com US$ 30 livres)** e **A7 (dono +
2ª pessoa para rotular no T+24)**. Abra UMA sessão da nuvem no repositório VAZIO do desafio, modelo **Opus**. Troque
só `<<COLE O ENUNCIADO INTEIRO>>`, `<<URL DO SITE DA EMPRESA>>` e `<<NOME DA 2ª PESSOA OU "nenhuma">>` e cole.

```text
Você é a sessão principal (M, o regente) de uma tentativa cronometrada: no máximo 58 min do primeiro ao último
commit (REGRA DURA), mirando ≥ 9,5 na Régua V4, tratada como a última tentativa. Responda ao dono em português
simples (ele não é da área). A cada ~5 min mande uma linha: hora de Brasília (UTC−3), marco atual,
adiantado/atrasado em min. TEMPO SOBRANDO NÃO É PARA PARAR: é para mais um ciclo medir → corrigir → medir.

Enunciado (literal):
<<COLE O ENUNCIADO INTEIRO>>

Régua V4 (nomes e pesos oficiais): Business & Challenge Fit 8% · Agentic Reasoning & Orchestration 15% (o Router
está aqui) · Context, Knowledge & RAG 10% · Tool & Action Engineering 10% · Security & Identity 13% · Memory, State
& Resilience 8% · Human Oversight & Risk Management 7% · Evaluation & Quality Engineering 14% · Observability,
Reliability & Cost 6% · Production Engineering 5% · Engineering Judgment 4%. Gates: Critical Security, Challenge
Fit, Evidence, Semantic Quality. O AVALIADOR NÃO RODA NADA E NÃO ASSISTE AO VÍDEO: a prova tem de estar escrita e
commitada. A correção da v4 (8,5) disse onde está a nota: QUALIDADE DAS RESPOSTAS (juiz 60% fundamentadas nos
oficiais; meta ≥ 90%), busca (Recall@3 0,49 → ≥ 0,85; MRR 0,61 → ≥ 0,80), memória (pass@1 54% → ≥ 85%), avaliação
independente (2 rotuladores, held-out ≥ 80, perguntas reais) e HONESTIDADE na entrega (números ruins ao lado dos bons;
procedência do kit declarada). Não infraestrutura.

Kit: maathmartins-ux/kit-preflight, branch kit-v5.1.0 (anexe com add_repo e copie o conteúdo para este repo, SEM o
histórico do kit e SEM docs/kit/; copie, sem editar, docs/kit/CHANGELOG.md como docs/KIT_CHANGELOG.md e
docs/kit/ENSAIO_V51.md e docs/kit/changelog.d/ para docs/: é a procedência que docs/PROCEDENCIA.md cita). Siga
docs/kit/PLAYBOOK.md À RISCA (linha do tempo §2, regras §3, planos B §4) e leia docs/kit/LICOES_V4.md. Prompts das
frentes: docs/kit/PROMPTS.md.

Passos (horários do PLAYBOOK §2):
1. T+0: copie o kit, `pip install -e ".[dev]"`, commit "chore: scaffold from entregar-desafio-cronometrado kit
   v5.1.0", `git tag clock-start`, push com a tag. Logo depois, em 2º plano:
   `mkdir -p var && python scripts/fetch_models.py --fast > var/fetch_models.log 2>&1 &` (e5-large + bge-m3-int8, 2,7 GB; a K
   roda `--choose-retriever --fast` no T+15 com eles já no cache). Não espere: siga para o passo 2.
2. `python scripts/cloud_probe.py --site <<URL DO SITE DA EMPRESA>>` e a sonda da API (1 caso ao vivo,
   --max-usd 0.2). `aborted_quota` ou erro de chave: PARE e avise o dono numa linha.
3. `python scripts/preflight.py` → commit.
4. Até T+7: docs/SPEC.md (desempates; fatos de referência que cada resposta oficial TEM de conter, escritos antes do
   código) + evals/cases.jsonl (official literais, replan ≥ 20, dependent ≥ 10, parallel, approval, memory ≥ 15 com
   `expects_fact`). Commit "spec".
5. T+7: worktree por frente R, K, T, Q, D (`git worktree add -b fork/<x> ../<repo>-<x> main`) e um subagente Opus em
   segundo plano por frente (bloco comum + bloco da frente + a SPEC). Em paralelo, subagentes Sonnet sem worktree:
   H1 e H2 (autores cegos, 40 casos cada) e P (40 perguntas reais de lojistas, com link). Grave os JSONL sem ler as
   frases: evals/heldout_blind.jsonl (H1+H2) e evals/real_questions.jsonl (P); commits "heldout" e "real".
6. Integre cada frente ao ficar pronta: `python scripts/check_ownership.py <x> --base main`, merge --no-ff,
   `python scripts/check.py`.
7. T+20: `python -m evals.run_evals --calibrate-gate --apply`; `make eval`; gate ≥ 90%.
8. T+23, em segundo plano: rodada 1 = `scripts/live_eval.sh --repeat 3` (com o split real) e
   `python -m evals.run_evals --live --ablate-replan --mode no_needs --split real --repeat 1 --max-usd 1`. Espere
   com Monitor (until), nunca sleep. Split com status ≠ complete: rode SÓ ele de novo.
9. T+24: avaliação humana independente pela PÁGINA (kit v5.2): `python scripts/label_page.py --n 10 --raters
   <<NOME DO DONO>>,<<NOME DA 2ª PESSOA>>` e publique var/rotulagem.html com o Artifact tool, com as `capabilities`
   que o script imprime (db com as regras + user). Mande o link ao dono (ele compartilha com a 2ª pessoa como quem
   pode usar a página, não editar). Cada um marca sozinho; ninguém vê a marcação do outro. Até T+40: leia a coleção
   `rotulos` com ArtifactData (`out_dir`) para var/rotulos.json, `python -m evals.label --import-page var/rotulos.json`
   e `python -m evals.label --report` (concordância e kappa entre humanos). Quem marcou sem conta do claude.ai manda o texto de "Copiar minhas
   respostas": grave em var/<nome>.txt e `python -m evals.label --import-text var/<nome>.txt`. Sem a página: o caminho antigo
   (`--export 10 --rater <nome>` e respostas em lotes de 10 no chat).
10. T+31: `python -m evals.failure_modes` e cada reprovação do juiz CASO A CASO (o `reason` e o `failure_type`):
    corrija a CAUSA no domínio (corpus, tool, regra, cartão de capacidades), com teste, o caso no texto do commit.
    Nunca ajuste genérico de prompt, nunca mexa em caso ou gate para passar.
11. T+39: `cp evals/results/judge.json evals/results/judge_r1.json`; rodada 2 só dos splits afetados
    (--repeat 3) + juiz; `python -m evals.judge_diff evals/results/judge_r1.json evals/results/judge.json`
    (docs/JUDGE_DIFF.md). Enquanto roda: `make video`, `python scripts/demo_md.py`, `python scripts/timesheet.py`.
12. T+46: `python scripts/check.py --docker --scale`; `python scripts/delivery_message.py --repo <url do repo>`;
    preencha à mão SÓ os textos {{...}} do README (§0 leitura do placar, §5 perguntas da entrevista com os números,
    §7 limitações: cada métrica abaixo da meta com a causa); commit de tudo que não é README.
13. T+51: `git tag clock-end` e push da tag; `make final` (README sozinho no último commit + push).
14. T+53: confira a CI do último commit no GitHub. Verde: pare. NADA depois de T+58.
15. Mande ao dono: o placar inteiro (bons e ruins), o texto de docs/ENTREGA.md, links do repo, da CI e do vídeo, e
    a nota que você espera por critério com o motivo.

Armadilhas já pagas (LICOES_V4.md): juiz sem o texto das fontes reprova o que é verdade (o kit grava `context` em
cada linha; confira que o judge.json da rodada 1 tem `saw_context` alto); clima/câmbio pela busca web inventa número
(LIVE_DATA=on); oferta de ação sem tool; regra da casa sem fonte (vai no cartão de capacidades); README misturado
com outro arquivo deixa a CI vermelha (make final); `pkill -f` mata o próprio shell; resposta em pt para pergunta
en; número somado pelo LLM (a tool devolve o total).

Regras que você não quebra: motor congelado (exceção: bug do ao vivo, com teste); gate nunca desce; held-out e
perguntas reais cegos; número só via fill_readme; nada de exemplo no produto; nenhuma resposta pronta no código;
comentário só com número medido; a mensagem de entrega sai com os números ruins e a procedência.
```
