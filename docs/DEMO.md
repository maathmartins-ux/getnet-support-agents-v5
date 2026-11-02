# Respostas reais — split `official`

Geradas de `evals/results/live_official.json` (provedor `anthropic`, status `complete`, gasto US$ 0.53) no commit `17254ba` em 02/11/2026 18:47 UTC. Nada aqui foi escrito à mão: é a saída do `POST /chat` com o LLM ligado, 1ª rodada de cada caso.

Estabilidade em 3 rodadas: pass@1 0.6667, pass^3 0.6; instáveis: official-02.

| caso | intenção | rota | ferramentas | handoff | veredito automático |
|---|---|---|---|---|---|
| `official-01` | knowledge | router → faq → escalation | — | sim | falhou: handoff, handoff_outcome |
| `official-02` | general | router → faq | — | não | OK |
| `official-03` | support | router → records | get_settlements | não | OK |
| `official-04` | knowledge | router → faq → escalation | — | sim | falhou: handoff, handoff_outcome |
| `official-05` | troubleshoot | router → records → faq | get_terminal_status | não | OK |
| `official-06` | knowledge | router → faq | — | não | OK |
| `official-07` | general | router → faq | — | não | OK |
| `official-08` | troubleshoot | router → records → faq → escalation | get_transactions, get_terminal_status | sim | falhou: handoff, handoff_outcome |
| `official-09` | knowledge | router → faq | — | não | OK |
| `official-10` | knowledge | router → faq | — | não | OK |

## official-01

**Pergunta:** What's the difference between the Get Clássica and the Get Smart?

**Intenção:** knowledge (esperada knowledge) · **rota:** router → faq → escalation · **replanos:** ['faq:not_in_sources->escalation'] · **motor:** table · **custo:** US$ 0.0038 · **latência:** 3.0 s

**Resposta:**

> I've handed this to a human agent (ticket T-3d2ccab9). The reply will show up in this conversation.

**Fontes:** <https://site.getnet.com.br/duvidas/get-smart/>; <https://site.getnet.com.br/duvidas/get-smart/>
**Checagens:** {'intent': True, 'handoff': False, 'handoff_outcome': False, 'language': True, 'numbers': True, 'claims': True}

## official-02

**Pergunta:** What's the weather forecast in Porto Alegre tomorrow?

**Intenção:** general (esperada general) · **rota:** router → faq · **replanos:** nenhum · **motor:** table · **custo:** US$ 0.0754 · **latência:** 26.6 s

**Resposta:**

> I couldn't find a reliable forecast for tomorrow in Porto Alegre. The sources I found are not up to date or don't clearly show tomorrow's date, so I can't confirm tomorrow's conditions, temperature or chance of rain.

**Fontes:** <https://www.wunderground.com/hourly/br/porto-alegre/date/2026-9-13>; <https://www.yr.no/en/forecast/daily-table/2-3452925/Brazil/Rio%20Grande%20do%20Sul/Porto%20Alegre/Porto%20Alegre>; <https://www.timeanddate.com/weather/@12964257/ext>; <https://www.meteoblue.com/en/weather/week/porto-alegre_brazil_3452925>; <https://www.worldweatheronline.com/porto-alegre-weather/rio-grande-do-sul/br.aspx>
**Checagens:** {'intent': True, 'handoff': True, 'handoff_outcome': True, 'language': True, 'numbers': True, 'claims': True}

## official-03

**Pergunta:** When will the money from yesterday's sales be deposited?

**Intenção:** support (esperada support) · **rota:** router → records · **replanos:** nenhum · **motor:** table · **custo:** US$ 0.0140 · **latência:** 7.1 s

**Resposta:**

> Yesterday's sales total 745.50. They are deposited on different dates:
>
> - **2026-11-01 (yesterday):** 60.00 for TX1005 (Pix, D+0).
> - **2026-11-02 (today):** 205.50 for TX1001 (120.00, debit) and TX1003 (85.50, debit). Both are D+1 business day.
> - **2026-12-01 (in 29 days):** 480.00 for TX1002 (credit, D+30).

**Checagens:** {'intent': True, 'handoff': True, 'handoff_outcome': True, 'language': True, 'tools': True, 'numbers': True, 'claims': True}

## official-04

**Pergunta:** Do I need a bank account to receive my sales via Pix?

**Intenção:** knowledge (esperada knowledge) · **rota:** router → faq → escalation · **replanos:** ['faq:not_in_sources->escalation'] · **motor:** table · **custo:** US$ 0.0042 · **latência:** 3.0 s

**Resposta:**

> I've handed this to a human agent (ticket T-ff99ec49). The reply will show up in this conversation.

**Fontes:** <https://site.getnet.com.br/duvidas/pix-mais-respostas/>; <https://site.getnet.com.br/duvidas/pix-mais-respostas/>; <https://site.getnet.com.br/pix/>
**Checagens:** {'intent': True, 'handoff': False, 'handoff_outcome': False, 'language': True, 'numbers': True, 'claims': True}

## official-05

**Pergunta:** My card machine won't connect to the internet, what should I do?

**Intenção:** troubleshoot (esperada troubleshoot) · **rota:** router → records → faq · **replanos:** nenhum · **motor:** llm · **custo:** US$ 0.0326 · **latência:** 11.5 s

**Resposta:**

> Only one of your machines has a connection problem.
>
> - **T1988A (Get Smart):** online, connected by Wi-Fi.
> - **T1988B (Get Clássica):** offline for 190 minutes. It connects by chip and shows no signal.
>
> For T1988B, check the SIM chip setup. This is the only troubleshooting source I found [sup-duvidas-06]:
> 1. With the machine off, open the back cover.
> 2. Insert the chip in the slot marked SIM1 or SIM2, with the metallic side facing down.
> 3. Close the cover, turn the machine on, and wait for it to connect to the data network.
> 4. When it shows a connected network (2G or 3G), it's ready to use.
> 5. Then run a communication test to check the chip's connectivity. The source doesn't list the test steps.
>
> If it stays offline, I can propose a technical support ticket for T1988B. It would only be a proposal, and nothing runs until you confirm it. Do you want me to propose it?

**Fontes:** <https://site.getnet.com.br/duvidas/>
**Checagens:** {'intent': True, 'handoff': True, 'handoff_outcome': True, 'language': True, 'tools': True, 'numbers': True, 'claims': True, 'completed': True}

## official-06

**Pergunta:** How does receivables advance (antecipação) work with Getnet?

**Intenção:** knowledge (esperada knowledge) · **rota:** router → faq · **replanos:** nenhum · **motor:** table · **custo:** US$ 0.0074 · **latência:** 5.4 s

**Resposta:**

> The sources don't explain the general mechanics of receivables advance. What they do say:
>
> - Under Central Bank Resolution 4.734 and Circular 3.952 (in force from June 7, 2021), merchants can use their card receivables in credit operations with authorized institutions, and the acquirer must register those receivables with a registry so they become a financial instrument that can be negotiated [sup-antecipacao-de-vendas-08].
> - Automatic Advance is a condition for the fee exemption on the "Receba Conforme suas Vendas" receiving plan. Because it involves credit approval, Getnet evaluates each contract individually and may or may not grant the product [sup-taxas-03].
> - When a loan is collateralized (gravame), all your sales on Getnet and other acquirers are received in your Get Conta, up to the loan's outstanding balance [sup-antecipacao-de-vendas-05].

**Fontes:** <https://site.getnet.com.br/duvidas/antecipacao-de-vendas/>; <https://site.getnet.com.br/duvidas/taxas/>; <https://site.getnet.com.br/duvidas/antecipacao-de-vendas/>
**Checagens:** {'intent': True, 'handoff': True, 'handoff_outcome': True, 'language': True, 'numbers': True, 'claims': True}

## official-07

**Pergunta:** What's the euro exchange rate today?

**Intenção:** general (esperada general) · **rota:** router → faq · **replanos:** nenhum · **motor:** table · **custo:** US$ 0.0040 · **latência:** 5.1 s

**Resposta:**

> There's no euro quote for today (Monday, 11/02/2026), so the latest available is from Friday, 10/30/2026. According to the Banco Central do Brasil (PTAX) closing bulletin, 1 EUR = R$ 6.0522 for sale and R$ 6.0505 for purchase (about R$ 6.05 either way).

**Fontes:** <https://www.bcb.gov.br/estabilidadefinanceira/historicocotacoes>
**Checagens:** {'intent': True, 'handoff': True, 'handoff_outcome': True, 'language': True, 'numbers': True, 'claims': True}

## official-08

**Pergunta:** My card machine is showing a transaction decline error.

**Intenção:** troubleshoot (esperada troubleshoot) · **rota:** router → records → faq → escalation · **replanos:** ['faq->escalation (plano: [])'] · **motor:** llm · **custo:** US$ 0.0416 · **latência:** 18.0 s

**Resposta:**

> Your account shows two declined sales today. Both were on terminal T1988A, which is online on Wi-Fi.
>
> - **TX1007** (credit, R$ 210,00): code 51 means the cardholder has insufficient funds or credit limit.
> - **TX1008** (debit, R$ 75,00): code 05 means the card's issuing bank did not authorize the sale.
>
> Both declines came from the card side, not from a connection problem.
>
> Terminal T1988B is offline. It has had no signal for 190 minutes. None of the declined sales were on it.
>
> I found no source in the help articles on what to do after a decline. I opened a case with a human agent (ticket T-56218993), and their reply will show up in this conversation.
>
> If you want, I can also propose a technical support ticket for T1988B. It would only go ahead after you confirm it.

**Fontes:** <https://site.getnet.com.br/duvidas/>
**Checagens:** {'intent': True, 'handoff': False, 'handoff_outcome': False, 'language': True, 'tools': True, 'numbers': True, 'claims': True}

## official-09

**Pergunta:** How many installments can I split a sale into with the crediário?

**Intenção:** knowledge (esperada knowledge) · **rota:** router → faq · **replanos:** nenhum · **motor:** table · **custo:** US$ 0.0057 · **latência:** 5.5 s

**Resposta:**

> With the crediário, the installment plan can go up to 48 installments on the credit card [prod-crediario-03][prod-crediario-01]. However, the actual limit depends on the card issuer, since each issuer sets its own installment limit under its credit policies [sup-crediario-03]. Interest rates may also vary by issuer [prod-crediario-03]. To see the exact interest and final amount, run a simulation on the terminal: insert the card, enter the amount, and choose credit > crediário [sup-crediario-03]. The simulation is for reference only and the issuer decides whether to approve the transaction [sup-crediario-03].

**Fontes:** <https://site.getnet.com.br/crediario/>; <https://site.getnet.com.br/crediario/>; <https://site.getnet.com.br/duvidas/crediario/>
**Checagens:** {'intent': True, 'handoff': True, 'handoff_outcome': True, 'language': True, 'numbers': True, 'claims': True}

## official-10

**Pergunta:** Can I sell through WhatsApp using the Payment Link?

**Intenção:** knowledge (esperada knowledge) · **rota:** router → faq · **replanos:** nenhum · **motor:** table · **custo:** US$ 0.0038 · **latência:** 4.8 s

**Resposta:**

> Yes. According to Getnet, you can make sales using WhatsApp, SMS or your preferred social network with payment links [prod-en-online-02]. The link is customizable with product details, and you choose the payment method, debit or credit [prod-en-online-02]. It also comes with security and anti-fraud tools [prod-en-online-02].

**Fontes:** <https://www.getnet.net/en/our-solutions/online-payments>
**Checagens:** {'intent': True, 'handoff': True, 'handoff_outcome': True, 'language': True, 'numbers': True, 'claims': True}
