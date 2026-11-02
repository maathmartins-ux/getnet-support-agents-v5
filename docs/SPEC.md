# Spec — Getnet Support Agents (v5)

Commitada antes de qualquer código. Congelada (OWNERSHIP.json): mudança aqui é decisão da sessão principal.

## Problema
Lojistas da Getnet perguntam sobre produtos (maquininhas, Pix, antecipação, crediário, link de pagamento), sobre o
próprio dinheiro e as próprias maquininhas, e às vezes sobre o mundo (clima, câmbio). Um Router decide quem
responde; o Knowledge responde com RAG sobre o site oficial; o Support lê os dados do cliente por tools; um agente de
escalonamento leva a um humano quando o sistema não consegue resolver com confiança.

## Taxonomia (intents) → plano inicial (agentes do motor: faq = Knowledge, records = Support, escalation = humano)

| intent | quando | plano |
|---|---|---|
| `knowledge` | pergunta sobre produto/serviço/regra da Getnet ("como funciona", "posso", "preciso de", "quantas parcelas") | faq |
| `support` | pede DADO do próprio cliente (vendas, depósitos/recebíveis, maquininhas, status) ou ação sobre ele | records |
| `troubleshoot` | SINTOMA de maquininha/transação do cliente ("não conecta", "erro", "recusada") | records → faq (needs) |
| `general` | assunto fora da Getnet com resposta pública (clima, câmbio, data) — LIVE_DATA (Open-Meteo, BCB PTAX) | faq com web/live_data; nunca abre caso |
| `human_request` | pede pessoa/atendente/ouvidoria | escalation |
| `multi` | duas perguntas independentes (produto + dado) no mesmo turno | faq ∥ records |
| `blocked` | guardrail (injeção, dado de outro cliente, fraude, abuso) | nenhum |

### Desempates (escritos antes do código)
1. Sintoma de maquininha ou de transação → `troubleshoot` (mesmo sem a palavra "minha").
2. Pergunta sobre o próprio dinheiro/venda/agenda/maquininha ("meu", "minhas vendas", "ontem", "quando cai") → `support`.
3. "Preciso de / posso / funciona" sobre produto ou regra → `knowledge` (ex.: "Preciso de conta para Pix?").
4. Clima, câmbio, cotação, notícia → `general`; nunca escala, nunca inventa número (dado só da API oficial com data).
5. Pedido explícito de humano vence tudo, salvo guardrail.
6. Idioma da resposta = idioma da pergunta (termo pt entre parênteses não muda o idioma).
7. Seguimento curto ("e quanto custa?", "e a outra?", "essa venda") herda o assunto do histórico.

## Dados do cliente (frente T; fixture `data/crm/`, datas RELATIVAS a hoje)
Cliente `cliente1988` (Loja do João, CNPJ fictício), e um segundo cliente `cliente2024` (isolamento: o registro de um
nunca aparece para o outro; "não encontrado" indistinguível).
- Maquininhas: `T1988A` Get Smart, Wi-Fi, online; `T1988B` Get Clássica, chip, OFFLINE há 190 min, sem sinal.
- Vendas de ontem: TX1001 débito R$ 120,00; TX1002 crédito à vista R$ 480,00; TX1003 débito R$ 85,50; TX1005 Pix R$ 60,00.
  Hoje: TX1006 crédito R$ 900,00 (cliente não reconhece); TX1007 crédito R$ 210,00 RECUSADA código 51 (saldo
  insuficiente do portador); TX1008 débito R$ 75,00 RECUSADA código 05 (não autorizada pelo emissor).
- Liquidação (tool calcula, o LLM não soma): débito D+1 útil, Pix D+0/D+1 conforme agenda, crédito D+30.
Tools (nomes congelados): leituras `get_transactions`, `get_settlements`, `get_terminal_status`; escritas com
confirmação `open_dispute` (contestar venda, risk high), `request_anticipation` (dinheiro, risk high),
`request_terminal_support` (chamado técnico). A identidade vem do servidor, nunca do schema.

## Cenários de aceite e FATOS DE REFERÊNCIA (a resposta TEM de conter)

| ID | Mensagem | Esperado | Fatos de referência |
|---|---|---|---|
| AC-01 | What's the difference between the Get Clássica and the Get Smart? | knowledge, en | as duas maquininhas descritas pelo site; Get Smart = smart (apps, gestão/estoque, nota fiscal), Get Clássica = maquininha tradicional (chip/Wi-Fi, comprovante impresso); fontes citadas |
| AC-02 | What's the weather forecast in Porto Alegre tomorrow? | general, en, sem caso | previsão de amanhã com data e fonte (Open-Meteo) ou declarar que não confirmou; nenhum número sem fonte |
| AC-03 | When will the money from yesterday's sales be deposited? | support, en, get_settlements | total de ontem R$ 745,50 e a data de cada modalidade (débito/Pix/crédito) como a tool devolveu |
| AC-04 | Do I need a bank account to receive my sales via Pix? | knowledge, en | Pix cai em conta (corrente, poupança ou de pagamento); a Get Conta / conta digital atende — conforme a fonte |
| AC-05 | My card machine won't connect to the internet, what should I do? | troubleshoot, en, get_terminal_status + faq | aponta T1988B offline (chip, sem sinal) e dá os passos de conexão do manual |
| AC-06 | How does receivables advance (antecipação) work with Getnet? | knowledge, en | antecipação = receber antes as vendas a prazo mediante taxa; pontual ou automática; conforme fonte |
| AC-07 | What's the euro exchange rate today? | general, en, sem caso | PTAX do BCB com a data do boletim (se hoje não há, o último dia útil, dito explicitamente) |
| AC-08 | My card machine is showing a transaction decline error. | troubleshoot, en, get_transactions | TX1007 código 51 e TX1008 código 05 com o significado e o que fazer |
| AC-09 | How many installments can I split a sale into with the crediário? | knowledge, en | até 48x (conforme fonte) |
| AC-10 | Can I sell through WhatsApp using the Payment Link? | knowledge, en | sim; o link é enviado por WhatsApp, redes sociais, e-mail, SMS |

Cada AC vira um caso `official-NN` em `evals/cases.jsonl` (mensagem literal).

## Splits de avaliação
official (10 literais) · replan (≥ 20: falha/sem fonte → próximo agente/humano) · dependent (≥ 10: só completa com 2
agentes, `must_include_agents`) · parallel (multi) · approval (escrita com confirmação, `pending_action`) · memory
(≥ 15, multi-turno, `expects_fact`) · guardrail (≥ 30) · heldout (cego, ≥ 80) · real (perguntas reais de lojistas,
fora do gate) · hard (fora do gate).

## Fora de escopo
- Executar de fato contestação/antecipação num sistema real (a escrita grava no CRM fictício após confirmação).
- Atendimento por voz; outros países além do Brasil.

## Divisão em forks

Ver OWNERSHIP.json. Contrato: `src/app/schemas.py` (inclui `RouterDecision` e `AgentName`), assinatura de
`pipeline.handle(req, user_id, identity_verified)` e status `ok|insufficient|error` dos agentes.
