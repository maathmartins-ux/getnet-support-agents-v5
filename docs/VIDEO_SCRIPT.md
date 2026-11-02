# Roteiro do vídeo (≤ 5 min)

Números falados no vídeo só os que estão no README (blocos do `fill_readme`), lidos na tela, nunca de cabeça.

| Tempo | Tela | Fala |
|---|---|---|
| 0:00–0:30 | README, tabela do topo | Problema: lojista Getnet pergunta de produto, do próprio dinheiro e do mundo; um Router decide quem responde. |
| 0:30–1:15 | `docs/ARCHITECTURE.md` diagrama 1 | Router → supervisor → Knowledge / Support / Escalation; replaneja por falha e por `needs`. |
| 1:15–2:00 | `/docs`, AC-01 e AC-09 | Knowledge com RAG: resposta com citação do site oficial; sem cobertura, oferece humano. |
| 2:00–2:45 | AC-03 e AC-05 | Support: `get_settlements` calcula as datas (o LLM não soma); `troubleshoot` lê `get_terminal_status` e puxa o manual via `needs`. |
| 2:45–3:30 | AC-07; contestação da TX1006 | `general` com PTAX do BCB e data; `open_dispute` pede confirmação e cai na fila do `/operator`. |
| 3:30–4:15 | `/operator` responde; `resume.py` retoma | Humano no laço: o plano salvo continua com a decisão do operador. |
| 4:15–5:00 | README §5 e resultados | Eval offline e ao vivo, ablação do replanejamento, o que não cobre (ADR 0007) e o piloto por intenção. |
