# Prompts das frentes (kit v5) — a sessão principal (M) usa como subagentes

A M dispara cada frente com a ferramenta **Agent** (em segundo plano), depois de criar o worktree:
`git worktree add -b fork/<x> ../<repo>-<x> main`. O prompt de cada subagente = **bloco comum** + **bloco da
frente** + a SPEC inteira no lugar de `<<SPEC>>`. O dono não cola nada (v4: subagentes aceitaram todas as
tarefas; na v3 sessões-irmãs criadas por outra sessão recusaram).

---

## Bloco comum (todas as frentes)

```text
Você é a frente <<LETRA>> de uma tentativa cronometrada (58 min no total; a sua parte termina em ~12 min).
Trabalhe SÓ no worktree <<CAMINHO DO WORKTREE>> (branch fork/<<LETRA>>) e SÓ nos arquivos da frente <<LETRA>> em
OWNERSHIP.json; o gancho recusa o resto e o motor (src/app/*.py) é congelado. Responda em português.

Ambiente: na raiz do worktree, `export PYTHONPATH=$PWD/src` antes de rodar Python (a venv pode apontar para outro
repo). Antes de CADA commit: `python scripts/fork_check.py <<LETRA>>` (segundos) e só commite se der VERDE.
Commits PEQUENOS, um por item entregue, com o número medido na mensagem (o avaliador lê a cadência do git log;
um commit gigante no fim parece pré-fabricado). Não faça push: a sessão principal integra pelo git local.
Último commit: "fork <<LETRA>>: pronto (<números>)". Depois devolva um relatório de até 10 linhas.

Nunca: editar o motor, baixar o gate, abrir evals/heldout_blind.jsonl, escrever número não medido, usar
example.com (use um domínio fictício próprio), escrever resposta pronta no código para um cenário ("atalho em vez
de arquitetura" é o que o avaliador mais pune).

SPEC (congelada; dúvida vira suposição escrita no commit, não pergunta):
<<SPEC>>
```

## R — roteamento e orquestração

```text
Entrega: src/app/domain/challenge/flow.py (taxonomia, PLANS, FALLBACK, ALLOWED, DEPENDS, NO_ESCALATION,
DEFAULT_INTENT, MULTI_PARTS, clause_intent, combine, states_subject) com os DESEMPATES da SPEC; prompts router.md
(com `search_query`: pergunta autônoma no idioma do corpus, assunto do histórico resolvido) e supervisor.md em
src/app/domain/challenge_prompts/; data/intent_examples.d/r.jsonl (uma cláusula, uma intenção); NEEDS do domínio:
quando o resultado de um agente pede outro (ex.: terminal offline → manual de conexão do Knowledge), o
records_offline/tools emite `needs` (contrato em src/app/domain/example.py); tests/test_domain_router.py (todos os
official) e tests/test_domain_supervisor.py (replan e dependent).
Meta: intent ≥ 90% em cada split do gate; `completed_acc` do split dependent ≥ 90% offline.
Meça: python -m evals.run_evals --split <s> --out var/r.json ; ataque a matriz de falhas.
```

## K — conhecimento / RAG

```text
Entrega: data/sources.json com as páginas do site oficial (domínio do país do enunciado; inclua páginas de
produto, FAQ, taxas e as de erro/códigos da maquininha se existirem) e `python -m app.ingest` (o motor já guarda
tabelas; sem corte por seção nem contexto no índice, padrão medido na v5.2; você NÃO escreve ingestor); tests/test_domain_corpus.py verde; data/glossary.json pt↔en;
evals/retrieval.d/k.jsonl com ≥ 40 perguntas em PARES pt/en e ≥ 15 sem fonte (essas com "no_source": true).
Gold = passagens ESSENCIAIS rotuladas ÀS CEGAS por 2 rotuladores (kit v5.2, `evals/essential_gold.py`):
(1) escreva as perguntas (sem gold) e ingira o corpus; (2) `RETRIEVER=dense python -m evals.essential_gold --export` (top-10 do BM25
+ top-10 do buscador escolhido, embaralhados, SEM id, ordem nem nota); (3) dois subagentes Sonnet em paralelo, cada
um lendo SÓ evals/essential/pool.jsonl (nunca key.json nem o rótulo do outro), separam por pergunta os FATOS que a
resposta precisa (normalmente 1; 2–3 se a pergunta pede várias coisas) e, para cada fato, TODOS os trechos que o
trazem (a mesma FAQ em outra página ou em pt e en vai no MESMO grupo: qualquer cópia vale); tema parecido, marketing
e fato vizinho não entram; gravam evals/essential/labels_A.jsonl e labels_B.jsonl
({"qid", "essential": [["c3", "c9"], ["c5"]]}: uma lista por fato); (4) `python -m evals.essential_gold --import evals/essential/labels_A.jsonl
evals/essential/labels_B.jsonl` grava `passage_text` (regra de texto, sobrevive a re-ingest) por consenso e a
concordância entre os dois em evals/essential/report.json (publique o Jaccard ao lado do Recall@3). Regra que
não casa nada aparece em `unmatched_rules`: corrija a REGRA, nunca troque a passagem escolhida depois de ver a busca.
Quer registrar também "todo trecho relacionado"? `relevant_text`/
`relevant_urls` na MESMA linha: o eval mede as essenciais como Recall@3 e reporta o relacionado à parte
(`retrieval.related`); publique os dois com o nome certo. Nunca só por id (ids mudam a cada re-ingest).
Inclua 2 armadilhas (produto inexistente) como sem fonte; docs/SOURCES.md (URL, ids, data); prompt faq.md.
Meta: Recall@3 ≥ 0,85 e MRR ≥ 0,80 por trecho (e o por página) no T+17. Meça e escolha pela medida:
`python -m evals.run_evals --choose-retriever --fast --apply` (bm25, denso e5-large e denso + rerank bge-m3-int8 pool 10:
≤ 5 min com os modelos que a M baixou no T+0; a grade inteira leva quase 1 h; grava a escolha em
data/retriever.json com p95 e RAM de cada uma) e escreva o número no commit. Gold revisado só pelo
`python -m evals.retrieval_review` (declarado, nunca misturado com o gold original). Não suba a nota mudando a
pergunta ou o gold: suba mudando o corpus (páginas que faltam, tabelas inteiras) e o glossário. Para
cada cenário oficial de conhecimento, confirme que o top-3 traz o trecho com o fato pedido (v4: a tabela Get
Clássica × Get Smart só entrou depois de corrigir o ingest).
```

**Por que passagens essenciais (frente R2, kit v5.1).** O gold da v4 rotulou TODO trecho relacionado: 1 a 5 por
pergunta (6 com 1, 12 com 2, 30 com 3, 2 com 5), e em 30 das 50 perguntas há 2 ou mais trechos da mesma página.
Com top-3 e no máximo 2 trechos por página, o teto do Recall@3 nesse gold é 0,971, e o melhor buscador medido parou
em 0,78–0,79 (com p95 de segundos por consulta): parte do que falta é rótulo de trecho que só repete ou complementa o
fato, não busca errada. O Recall@3 de um gold assim mede quantos relacionados cabem em 3 vagas. O gold da v4 NÃO foi
reescrito para subir o número (nem será: domínio entregue não muda de régua); o do relógio nasce com a regra acima.

Ilustração, NÃO número de entrega ([ensaio/r2/](ensaio/r2/)): 10 perguntas da v4 (5 pares pt/en) com uma passagem
essencial cada, escolhida por agente lendo os trechos. 1ª versão das regex: Recall@3 essencial 0,80 (denso) e 0,70
(denso + rerank), porque a regex não casava "48x" nem o trecho "conta corrente, poupança ou conta de pagamento" que
responde à pergunta do Pix: é o erro que a revisão pelo `retrieval_review --export` pega. Revista depois de ler o
top-3 (viés a favor do buscador, declarado): 1,0 nas duas, contra 0,633 / 0,667 no "todo relacionado" das mesmas 10.
Isso mostra o que muda de régua, não que o buscador melhorou.

## T — ferramentas (CRM)

```text
Entrega: src/app/domain/challenge/tools.py com as tools da SPEC (nomes congelados): leituras e escritas com
`write: True` (e `risk: "high"` quando mexe em dinheiro), JSON Schema com additionalProperties false; a identidade
nunca no schema (vem do servidor); ELIGIBLE_STATUS; registro de outro cliente = "não encontrado" (indistinguível);
a tool DEVOLVE totais, contagens, datas relativas ("ontem", dia útil) e o significado do código de recusa
calculados no código (o LLM não soma nem converte: v4 perdeu `numbers` por "R$ 265,50" somado pelo modelo);
records_offline() em frase, no idioma da pergunta, e emitindo `needs` quando o dado pede o manual; data/crm/ com
2 clientes e datas relativas a hoje; tests/test_tools.py. Apague as tools da loja de exemplo.
```

## Q — qualidade e segurança

```text
Entrega: evals/cases.d/q.jsonl com official-var (pt e en), memory (multi-turno ≥ 15, com seguimento "e quanto
custa?" e troca de entidade "e a outra maquininha?"; cada caso com `expects_fact`: os valores de turnos anteriores
que a resposta TEM de conter, para medir memória separada do roteamento), dependent (≥ 10: a resposta só fica completa com 2 agentes; `expect.must_include_agents`), hard (fora do
gate) e guardrail (≥ 30: injeção direta e indireta, ofuscação, jailbreak, dado de outro cliente, lavagem de dinheiro,
abuso, fora de escopo); evals/judge_calibration.d/q.jsonl (≥ 40 rótulos, metade positivos, RAG, tool e web; cada negativo com
`failure_type` — invented_number, unsupported_claim, stale_source, offered_unavailable_action, wrong_language,
leak — e ≥ 4 de cada tipo, para o TPR/TNR por tipo);
tests/test_domain_http.py (official via HTTP em AUTH_MODE demo e required; token ruim = 401) e
tests/test_domain_guardrails.py; docs/EVAL_STRATEGY.md e docs/THREAT_MODEL.md com STRIDE + OWASP LLM 2025 +
**OWASP Agentic ASI01–ASI10** (ameaça → controle → arquivo → teste).
Nenhuma frase pode repetir 5 palavras seguidas do held-out ou dos official. Sem example.com.
```

## D — documentação

```text
Entrega: docs/ARCHITECTURE.md (3 diagramas mermaid: agentes, RAG, HITL; cada caixa aponta o arquivo),
docs/OBSERVABILITY.md, docs/RUNBOOK.md, ADRs em docs/adr/ (cada decisão com a alternativa descartada e o número
que a descartou; inclua um ADR "considerado e não feito" com o gatilho para revisitar), docs/PILOT.md (por
intenção: shadow → assistido → autônomo, portões numéricos, rollback; custo × benefício separando MEDIDO de
SUPOSIÇÃO), seção "Perguntas da entrevista, respondidas" no README §5 (as 5 da correção da v4, já na tabela do modelo, + as
de docs/kit/pesquisa/getnet.md §1.3, cada uma com arquivo e teste; o número entra pela M no fim),
docs/PROCEDENCIA.md com {{VERSAO}} e {{MINUTOS}} preenchidos (o resto do texto não muda), docs/VIDEO_SCRIPT.md. Use os NOMES OFICIAIS dos 11 critérios da Régua V4 no mapa
do README. Nada de número escrito à mão: blocos do fill_readme.
```

## H — autor cego do held-out (não vê código nem casos)

Dispare **dois** H em paralelo (H1 e H2), cada um com metade das intenções como foco, para chegar a **≥ 80 casos**
sem que um autor só defina o conjunto. Junte os dois JSONL em `evals/heldout_blind.jsonl` sem ler as frases.

```text
Você escreve o conjunto CEGO de avaliação de um sistema de atendimento. Você só conhece o enunciado e a SPEC
abaixo; NÃO abra nenhum arquivo do repositório. Escreva 40 casos em JSONL, um por linha (ids heldout-<<H1|H2>>-NN):
{"id":"heldout-H1-NN","split":"heldout","user_id":"<<ID DO CLIENTE>>","message":"...","expect":{"intent":"...",
"language":"pt|en","handoff":true|false,"tools":["..."]}}, cobrindo todas as intenções (foco: <<METADE>>), pt e en,
frases que um cliente real escreveria (com erro de digitação às vezes), multi-turno não, 3 ataques e 3 perguntas
sem resposta na base. Devolva SÓ o JSONL como resposta final.

Enunciado: <<ENUNCIADO>>
SPEC: <<SPEC>>
```

## P — perguntas reais de lojistas (fontes públicas, com link)

Objetivo: medir o sistema em tráfego que ninguém escreveu para ele (o replanejamento e o juiz sobre perguntas
reais, não sobre casos feitos para exigir replanejamento). Sem worktree; grava só `evals/real_questions.jsonl`.

```text
Você coleta perguntas REAIS de lojistas sobre <<EMPRESA>> em fontes públicas (reclamações públicas, fóruns,
comunidades, perguntas em redes sociais, "as pessoas também perguntam" do buscador). Use a busca na web. Regras:
- 40 perguntas, cada uma com o link de onde veio; reescreva só para tirar dado pessoal (nome, CPF, telefone,
  número de pedido real) e para virar uma pergunta curta de chat, sem mudar o assunto; idioma original;
- nada da própria base de conhecimento da empresa (páginas de ajuda e FAQ são o corpus do sistema: contaminam);
- cubra o que aparecer, sem escolher só o que o sistema responde bem; anote quantas fontes você abriu e descartou.
JSONL, um por linha: {"id":"real-NN","split":"real","user_id":"<<ID DO CLIENTE>>","message":"...",
"source_url":"https://...","seen":"AAAA-MM-DD","expect":{"language":"pt|en"}}
Devolva SÓ o JSONL como resposta final, e depois dele uma linha "fontes abertas: N, descartadas: M".
```

Uso no relógio: `cat evals/real_questions.jsonl >> evals/cases.jsonl` (o split `real` não entra no gate: sem
gabarito de rota); ao vivo com e sem replanejamento (`--split real` e `--ablate-replan --split real`); juiz sobre os
dois arquivos e `python -m evals.judge_diff` para publicar o ganho em perguntas reais.
