# Piloto — shadow → assistido → autônomo, por intenção

Os portões abaixo são METAS de decisão, não medidas. As medidas atuais estão em `evals/results/` e no README §0.

| Fase | O que o lojista vê | Quem responde | Portão para avançar (por intenção) | Rollback |
|---|---|---|---|---|
| 1. Shadow (2 semanas) | resposta do atendente humano | o sistema responde em paralelo, só no log (`/audit`) | juiz ≥ 90% fundamentado em amostra diária de 50; concordância humano × juiz (kappa) ≥ 0,7; zero vazamento entre clientes | desligar a flag da intenção |
| 2. Assistido | resposta do sistema, aprovada pelo atendente | sistema rascunha; humano aprova/edita | taxa de edição < 15%; tempo médio de atendimento cai; nenhuma escrita sem confirmação | voltar a shadow na intenção |
| 3. Autônomo | resposta do sistema | sistema; handoff quando o portão sem fonte recusa | pass^3 ≥ 90% no split da intenção; reclamação ≤ baseline humano | voltar a assistido |

Ordem sugerida: `knowledge` e `general` primeiro (só leitura, fonte citada); `support` de leitura depois;
`troubleshoot` (dois agentes) depois; escritas (`open_dispute`, `request_anticipation`) ficam sempre com confirmação
do lojista e, se `risk: high`, com quatro olhos humanos (ADR 0006).

## Custo × benefício

| Item | Tipo | Valor |
|---|---|---|
| Custo por turno resolvido | MEDIDO | `evals/results/live_*.json` (`cost_usd` por linha) e README §0 |
| Latência p95 por turno | MEDIDO | `evals/results/latest.json`, `/metrics` |
| Fração resolvida sem humano | MEDIDO no eval, não em produção | handoff por split no README |
| Custo do atendimento humano por contato | SUPOSIÇÃO | a preencher com o dado da operação Getnet |
| Volume de contatos por intenção | SUPOSIÇÃO | idem |

## Sinais de parada (qualquer fase)
- vazamento de dado de outro cliente (1 caso basta);
- escrita executada sem confirmação;
- número em resposta sem fonte (`unsupported_numbers`) acima de 5% em um dia.
