# Roteiro da tentativa (kit v5.1) — 100% na nuvem, ≤ 58 min, mirando ≥ 9,5

Escrito a partir da Getnet v4 (34 min do 1º ao último commit, CI verde; lições em [LICOES_V4.md](LICOES_V4.md))
e da leitura de 28 soluções públicas do mesmo case ([pesquisa/getnet.md](pesquisa/getnet.md),
[pesquisa/formato_swarm.md](pesquisa/formato_swarm.md)). Cada regra abaixo existe porque a falta dela custou nota
ou tempo. O PC só abre o Chrome: nenhum fork, teste ou Docker roda nele.

Prompt da sessão principal pronto para colar: [V5_PROMPT_M.md](V5_PROMPT_M.md). Prompts das frentes:
[PROMPTS.md](PROMPTS.md). Operação pelo Chrome: [CHROME.md](CHROME.md).

**Três fatos que mudam a estratégia** (pesquisa de 01/11/2026):
1. O avaliador da Régua V4 **não roda nada e não assiste ao vídeo** ("Não executei build nem testes", "Vídeo …
   não assistido"). A nota sai do que está ESCRITO e COMMITADO: respostas reais em `docs/DEMO.md`, números em
   `evals/results/`, prova do relógio em `docs/TIMESHEET.md`.
2. Ele pune **atalho em vez de arquitetura** ("resolvem casos por atalho, em vez de pela arquitetura"), resposta
   em pt para pergunta em en, Support que não lê o dado do cliente, HITL que não volta ao fluxo, memória ausente.
3. Nenhuma nota ≥ 9 na Régua V4 foi feita em 60 min. O 9,5 público (nelsondell) perdeu meio ponto em: escala
   presa ao armazenamento, suíte que precisava de rede para começar, factual sem validação humana.

---

## 0. Antes do relógio (na véspera ou até T−30 min). Nada disto conta no tempo.

| # | O quê | Como saber que está feito |
|---|---|---|
| A1 | **Ambiente da nuvem com rede** para o site da empresa e para as APIs de dado ao vivo (`olinda.bcb.gov.br`, `geocoding-api.open-meteo.com`, `api.open-meteo.com`). Menu do ambiente → *Network access*: Full, ou os domínios em *Allowed domains*. | `python scripts/cloud_probe.py --site <url>` sem FALTA |
| A2 | **Chave do LLM do app** nas variáveis do ambiente: `APP_ANTHROPIC_API_KEY` (nunca no chat). Opcional: juiz de outra família (`JUDGE_PROVIDER=openai_compat`, `JUDGE_BASE_URL`, `JUDGE_MODEL`, `JUDGE_API_KEY`). | sonda: "chave do LLM do app" OK |
| A3 | **Repositório vazio do desafio**, público, com o app do Claude com push. | a sessão principal faz `git push` |
| A4 | **Sonda verde** numa sessão da nuvem: `python scripts/cloud_probe.py --site <url>` | `AMBIENTE PRONTO` |
| A5 | **PC só com o Chrome** (sem app desktop, sem Docker Desktop). | > 3 GB livres |
| A6 | **Orçamento, em DUAS contas separadas.** (1) Plano/créditos do Claude (claude.ai → Configurações → Uso; a tela do dono é em **reais**, limite R$ 130 na v4). (2) **API da Anthropic** (console.anthropic.com → Limits), que paga o eval ao vivo e o juiz: ≈ US$ 6 por rodada completa (`live_eval.sh`, teto padrão US$ 10), **mais ~US$ 8 se houver ensaio**. Confira o limite da API ANTES: no v5 ele acabou no meio do ensaio ("regain access on 2026-12-01") e nenhuma rodada ao vivo rodou depois. | os dois limites conferidos; `python -m evals.run_evals --live --split official --repeat 1 --max-usd 0.2` responde sem `aborted_quota` |
| A7 | **Página de avaliação testada antes do relógio** (`scripts/label_page.py`, publicada com o Artifact tool): dono e 2ª pessoa abrem o link e marcam 2–3 respostas de teste; a sessão lê a coleção `rotulos` e vê as duas fichas. Teste feito em 02/11/2026 com o ensaio (10 respostas). | duas fichas em `rotulos` |
| A7b | **Dono disponível 10 min entre T+24 e T+40** para conferir 10 respostas (passa/falha). **Segunda pessoa** (amigo, colega) para conferir as mesmas 10 no mesmo horário: a avaliação pediu 2 rotuladores com concordância entre eles. Sem a 2ª pessoa, o placar mostra "1 rotulador" como abaixo da meta. | combinado |
| A8 | **Limite da API com folga de US$ 30** (ver o orçamento no §2) | sonda da API sem `aborted_quota` |

---

## 1. Quem faz o quê (orquestração da v4, que funcionou)

A sessão principal (**M**, o regente) faz SPEC, integração, medição e README. As frentes são **subagentes da
própria M** (ferramenta Agent, em segundo plano), cada uma num `git worktree` com branch `fork/<x>`; a M integra
localmente com `scripts/check_ownership.py <x> --base main` e merge `--no-ff`. Não há sessão-irmã nem prompt
colado pelo dono (na v3, sessão criada por outra sessão recusou tarefa; na v4, subagentes não recusaram).

| Frente | Dono de (OWNERSHIP.json) | Entrega | Pronto na v4 |
|---|---|---|---|
| **H** autor cego | `evals/heldout_blind.jsonl` (devolve o JSONL; a M commita sem ler) | 24 casos que só viram enunciado + SPEC | T+3 |
| **R** roteamento | `domain/challenge/flow.py`, prompts router/supervisor/geral, `data/intent_examples.d/r.jsonl`, testes do router/supervisor, **`needs` do domínio** | intent ≥ 90% nos splits do gate; casos `dependent` | T+4 |
| **K** conhecimento | `data/sources.json`, `data/knowledge/**`, glossário, `evals/retrieval.d/**` (gold por **regra**: `relevant_urls`/`relevant_text`), prompt faq, `docs/SOURCES.md` | Recall@3 ≥ 0,7 medido no T+15, com o número no commit | T+6 (0,318; 0,486 após integração) |
| **T** ferramentas | `domain/challenge/tools.py`, `data/crm/**`, prompt records, `tests/test_tools.py` | leituras + escritas com confirmação; tool devolve totais e datas calculadas (o LLM não soma) | T+4 |
| **Q** qualidade e segurança | `evals/cases.d/**`, calibração do juiz, testes HTTP e de guardrail, EVAL_STRATEGY, THREAT_MODEL (com OWASP Agentic ASI01–10) | official-var, memory ≥ 12, guardrail ≥ 30, hard, `dependent`, fatos de referência dos 10 cenários | T+6 |
| **D** documentação | ARCHITECTURE, OBSERVABILITY, RUNBOOK, ADRs (inclui "considerado e não feito"), PILOT, perguntas da entrevista no README | docs só com o que o código faz | T+5 |

O motor (`src/app/*.py`), scripts, runner do eval e fixtures são **congelados** durante o relógio
(`.claude/hooks/ownership_guard.py` recusa a edição; `check_ownership.py` recusa o merge). Exceção: bug de motor
achado pelo eval ao vivo vira commit da M com teste de regressão e o número no commit (v4: 3 correções assim).

---

## 2. Linha do tempo (T = primeiro commit; **regra dura: nada depois de T+58**)

A v4 parou no T+34 com tempo sobrando e nota 8,5, segurada pela **qualidade das respostas** (juiz 60% nos oficiais),
não pela infraestrutura. Por isso a v5 usa o relógio inteiro num ciclo **medir → corrigir a causa → medir de novo →
publicar o antes e o depois**, duas vezes. Tempo sobrando vai para esse ciclo, nunca para parar mais cedo.

| Quando | Quem | O quê | Saída verificável |
|---|---|---|---|
| T+0 | M | commit `chore: scaffold from entregar-desafio-cronometrado kit v5.1.0` + `git tag clock-start` + push com a tag | 1º commit |
| T+0 | M (2º plano) | `mkdir -p var && python scripts/fetch_models.py --fast > var/fetch_models.log 2>&1 &` — baixa e5-large + bge-m3-int8 (2,7 GB; 34 s na nuvem em 02/11/2026) para o `--choose-retriever --fast` da K não esperar download. O cache de vetores (`var/embeddings` do repositório principal) é compartilhado com os worktrees | `MODELOS PRONTOS` no log |
| T+0→T+2 | M | `python scripts/preflight.py` e **a sonda da API** (`run_evals --live --split official --repeat 1 --max-usd 0.2` com 1 caso): `aborted_quota` = PARE e avise o dono (sem API não há como passar do gate semântico) | `PRÉ-VOO OK` |
| T+2→**T+7** | M | SPEC com desempates e **fatos de referência** de cada cenário oficial + `evals/cases.jsonl` (official literais, replan ≥ 20, dependent ≥ 10, parallel, approval, memory ≥ 15 com `expects_fact`) | commit `spec` |
| T+7 | M | dispara em segundo plano: R, K, T, Q, D (Opus) e H1, H2, P (Sonnet: escrevem só JSONL) | 8 subagentes |
| T+7→T+19 | frentes | commits pequenos **por item**; `fork_check.py <x>` antes de cada um; último `fork <x>: pronto`. K: `--choose-retriever --fast --apply` (3 configurações, ≤ 5 min; a grade inteira leva quase 1 h) com o número no commit | branches `fork/*` |
| T+10→T+20 | M | integra cada frente ao ficar pronta; H1+H2 → `evals/heldout_blind.jsonl` (≥ 80, sem ler); P → `evals/real_questions.jsonl` | `main` verde |
| T+20→T+23 | M | `run_evals --calibrate-gate --apply`; `make eval`; gate ≥ 90% | commit com o gate |
| **T+23→T+31** | M (2º plano) | **rodada 1**: `scripts/live_eval.sh --repeat 3` (inclui `real`; todos os splits num processo só: com o denso, um processo por split estourava a RAM), ablação `--ablate-replan --mode no_needs --split real`, juiz (`judge.json`) | `live_*.json`, `judge.json` |
| T+24→T+40 | **dono** + 2ª pessoa + M | conferência pela página (`scripts/label_page.py --n 10`, 10 situações, ~7 min cada, prazo T+40; decisão do dono: 10); sem a página, `evals.label --export 10 --rater dono` no chat | `human_review.json` |
| T+31→T+39 | M | `evals.failure_modes` + reprovações do juiz **caso a caso**: corrigir a CAUSA (fonte errada, número reformatado, afirmação fora do trecho, ação oferecida sem tool) no domínio (corpus, tool, regra, cartão de capacidades); nunca ajuste genérico de prompt; teste por correção | commits `fix:` com o caso no texto |
| **T+39→T+46** | M (2º plano) | **rodada 2** só dos splits afetados (`official`, `memory`, os que caíram) `--repeat 3` + juiz; copie o `judge.json` da rodada 1 para `judge_r1.json` antes; `python -m evals.judge_diff evals/results/judge_r1.json evals/results/judge.json` → `docs/JUDGE_DIFF.md` | antes × depois |
| T+40→T+46 | M | `make video`; `scripts/demo_md.py`; `scripts/timesheet.py` | DEMO, TIMESHEET, MP4 |
| T+46→T+51 | M | `check.py --docker --scale`; `scripts/delivery_message.py --repo <url>` (placar bom e ruim + procedência); commit de tudo que não é README | `CHECK VERDE` |
| T+51→T+53 | M | `git tag clock-end`; `make final` (README sozinho no último commit + push) | `fill_readme --check` OK |
| T+53→T+57 | M | CI do último commit no GitHub; vermelho → plano B | Actions verde |
| **T+58** | — | **nada depois**. Mensagem ao dono com o placar inteiro | — |

Orçamento da API para a v5 (conta separada do plano; console.anthropic.com → Limits): rodada 1 ≈ US$ 8 (com `real` e
ablação), juiz ≈ 2, rodada 2 ≈ 4, juiz ≈ 1 → **≈ US$ 15; deixe pelo menos US$ 30 livres** antes do T+0.

**Relatório ao dono a cada ~5 min**, em horário local (Brasília = UTC−3): marco atual, adiantado/atrasado em
minutos, próximo passo. Uma linha. O dono acompanha pelo celular.

---

## 3. Regras para todas as frentes e para a M

1. **Motor congelado** durante o relógio (exceção: bug do ao vivo, com teste e número no commit).
2. **Gate nunca desce.** Abaixo de 90%, corrige-se o domínio pela matriz de falhas.
3. **Held-out cego.** O teste de contaminação reprova frase copiada para regra ou exemplo.
4. **Número só de arquivo commitado.** README só por `fill_readme.py`; o check reprova divergência.
5. **README sozinho no último commit** (`make final`). Qualquer commit depois exige rodar de novo (v4: CI
   vermelha 2 vezes por isso).
6. **Nada de exemplo no produto**: nem `example.com` em caso de teste (use domínio fictício próprio).
7. **Comentário e commit só com número medido.**
8. **Atalho não:** nenhuma resposta escrita no código para um cenário; o Support sempre lê o dado do cliente;
   respostas no idioma da pergunta.
9. **Processos:** nunca `pkill -f "<texto do próprio comando>"` (mata o shell); mate por PID:
   `ps -eo pid,args | grep "[r]un_evals"`. Espera longa: Monitor com `until`, nunca `sleep` encadeado.
10. **Rodada ao vivo só vale se terminou limpa.** `status: complete` e `llm_errors` ~0. `degraded` (chamadas perdidas),
    `aborted_quota` (limite da API) e `aborted_*` vão para `.degraded.json`/`.aborted_*.json` e NUNCA substituem um
    resultado completo; não commite nem cite número de rodada assim (a v5 descartou uma por isso).
    **Juiz interrompido** (`judge.json` com `aborted_quota`/`aborted_llm_error`): o parcial fica gravado; com o limite
    da API liberado, `python -m evals.judge <os mesmos live_*.json> --resume` julga só o que faltou (ensaio v5.1: o
    limite acabou no 99º julgamento e, antes desta regra, tudo se perdia).
11. **Mudou o motor, meça num domínio real antes de declarar melhoria.** 487 testes verdes não pegaram 3 regressões
    que o ensaio sobre a v4 achou em 1 hora (`ENSAIO_V5.md`). Use `docs/kit/ENSAIO_V5.md` como roteiro.
12. **venv certa:** o `check.py` recusa se o pacote `app` vier de outro repo (`pip install -e .` no repo atual).

---

## 4. Planos B

| Se… | Então |
|---|---|
| SPEC não sai até T+6 | congelar taxonomia + 10 official e soltar as frentes; casos extra pela Q |
| frente sem "pronto" até T+18 | integrar o que houver; declarar no README |
| gate < 90% no T+22 | R e Q nas 2 maiores confusões; no T+30 congela e declara |
| split ao vivo `aborted_max_usd` | rodar SÓ ele de novo: `run_evals --live --split <s> --max-usd 2 --repeat 3` |
| APIs de clima/câmbio bloqueadas | `LIVE_DATA=off` (cai na busca web) e declarar `unsupported_numbers` como limite |
| dono indisponível no T+24 | pular a rotulagem humana; declarar "factual sem validação humana" como limite |
| CI vermelho no T+53 | `git revert` do último commit de código, `make final` de novo |
| rodada 2 não termina até T+46 | publicar só a rodada 1 com o diff "não medido"; o placar mostra o que ficou abaixo |
| API com limite atingido no T+0 | parar: sem LLM o sistema roda no determinístico e o gate semântico não passa; remarcar |

---

## 5. O que cada critério da Régua V4 exige (nomes e pesos oficiais) e onde fica a prova

| Critério (peso) | Evidência escrita no repositório | Frente |
|---|---|---|
| Business & Challenge Fit (8%) | `docs/DEMO.md` com as respostas REAIS dos 10 cenários; Support lendo o dado do cliente; `docs/PILOT.md` (shadow → assistido → autônomo); clima/câmbio de API oficial com data | M, D |
| Agentic Reasoning & Orchestration (15%) — inclui o Router | supervisor que observa e replaneja por falha E por achado (`needs`); split `dependent`; ablação por conclusão (`--mode no_needs`); orçamento por turno (`budget_exhausted`); matriz de confusão do router | R, M |
| Context, Knowledge & RAG (10%) | trechos literais com URL/data/SHA e contexto de seção; Recall@k por trecho e por página; gold por regra; `--compare-retrievers`; portão calibrado (`--apply`) | K |
| Tool & Action Engineering (10%) | JSON Schema estrito, identidade fora do schema, escrita com confirmação e quatro olhos; detector de ação alegada sem execução | T |
| Security & Identity (13%) | JWT, rate limit, guardrails além de regex, PII mascarada; OWASP Agentic ASI01–10 com teste por linha; LGPD (`DELETE /me/conversations/{id}`, retenção) | Q, M |
| Memory, State & Resilience (8%) | split `memory` ao vivo; pergunta autônoma (`search_query`); volume persistente; réplica cai e a conversa segue | R, Q |
| Human Oversight & Risk Management (7%) | fila persistida, operador responde e o PLANO retoma; caso só fecha com prova; ataque não abre caso | T, Q |
| Evaluation & Quality Engineering (14%) | gate no CI + **replay da gravação ao vivo** no CI; pass^3; juiz com canários (e de outra família se houver chave); **validação humana** (`human_review.json`); `FAILURE_MODES.md` | Q, M |
| Observability, Reliability & Cost (6%) | trace_id, `/metrics`, `/ready`, custo por turno resolvido e por intenção, dashboard Grafana provisionado | M |
| Production Engineering (5%) | CI verde com rede cortada, SBOM e trivy, actions por SHA, overlay endurecido, 2 réplicas | M |
| Engineering Judgment (4%) | ADRs com o número que decidiu (inclui "considerado e não feito"); "Perguntas da entrevista, respondidas"; limitações com números; `docs/TIMESHEET.md` | D, M |

Gates da V4 (feedback público): **Critical Security**, **Challenge Fit** ("o núcleo foi implementado no próprio
código"), **Evidence** ("logs de execução real commitados"), **Semantic Quality** ("não comprovado" quando não há
medição de qualidade das respostas). O kit v5 tem um artefato para cada um.

---

## 6. Depois do último commit

Nada no repositório do desafio. Balanço e lições no repositório do kit.
