Olá! Segue a minha entrega do desafio.

Repositório: https://github.com/maathmartins-ux/getnet-support-agents-v5
Como avaliar em 5 minutos: a seção 0 do README; as respostas reais dos cenários oficiais estão em docs/DEMO.md e a linha do tempo em docs/TIMESHEET.md.

Resultados medidos (todos gerados de evals/results/, no README):
- Juiz: respostas oficiais fundamentadas: 1.00 (meta 0.90)
- Oficiais: números com base na evidência: 96.7% (meta 95.0%)
- Memória ao vivo: números com base: 100.0% (meta 95.0%)
- Held-out cego: casos: 80 (meta 80)
- Rotuladores humanos independentes: 2 (meta 2)

Onde ainda está abaixo da meta, ou não foi medido:
- Oficiais: pass^k (todas as rodadas passam): 0.60 (meta 0.90)
- Memória ao vivo: pass@1: 0.72 (meta 0.85)
- Busca: Recall@3: 0.84 (meta 0.85)
- Busca: MRR: 0.71 (meta 0.80)
- Held-out cego: intenção: 67.5% (meta 85.0%)
- Juiz × humano: kappa: 0.58 (meta 0.80)

Procedência: o primeiro commit traz um kit próprio, que evoluiu a partir das correções das minhas entregas anteriores deste desafio. O que veio do kit, o que foi feito no relógio e como comparar pela primeira entrega estão em docs/PROCEDENCIA.md. Relógio: 45 min do primeiro ao último commit (tags clock-start/clock-end).

Obrigado!
