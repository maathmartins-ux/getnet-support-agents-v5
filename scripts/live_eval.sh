#!/usr/bin/env bash
# Eval ao vivo por split + juiz + README (Linux/macOS/Git Bash). Mesmo comportamento de live_eval.ps1.
#
# Uso:
#   scripts/live_eval.sh --max-usd 10        # ~6 medidos na v4; splits ao mesmo tempo num processo, cada um com a sua cota
#   scripts/live_eval.sh --splits official,replan --workers 4 --repeat 1   # padrão 3 (pass^3); 1 = smoke
#   scripts/live_eval.sh --dry-run            # mostra splits e teto, sem gastar
#
# - Lê o .env do projeto SEM imprimir valores (a chave nunca aparece no console nem no log).
# - O teto vale para a rodada inteira: 80% dividido entre os splits (num processo só), 20% para o juiz.
# - Sem chave: run_evals sai com código 2 e mensagem clara; o script para sem traceback.
set -euo pipefail

SPLITS="" MAX_USD="10" WORKERS="4" REPEAT="3" NO_JUDGE=0 DRY=0  # repeat 3: pass^3 (custo ~3x; --repeat 1 = smoke)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --splits) SPLITS="$2"; shift 2 ;;
    --max-usd) MAX_USD="$2"; shift 2 ;;
    --workers) WORKERS="$2"; shift 2 ;;
    --repeat) REPEAT="$2"; shift 2 ;;
    --no-judge) NO_JUDGE=1; shift ;;
    --dry-run) DRY=1; shift ;;
    *) echo "opção desconhecida: $1" >&2; exit 64 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# LIVE_EVAL_PY: intérprete explícito (CI Linux não tem .venv; Getnet v3 31/10/2026: CI vermelho do G1 ao fim)
PY="${LIVE_EVAL_PY:-$ROOT/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$ROOT/.venv/Scripts/python.exe"  # Git Bash no Windows
[[ -x "$PY" ]] || { echo "Falta a venv em $ROOT/.venv ou LIVE_EVAL_PY (references/brief-de-fork.md, seção Ambiente)."; exit 1; }

if [[ -f .env ]]; then  # exporta KEY=VALUE sem ecoar nada
  while IFS='=' read -r key value; do
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] && export "$key=${value%$'\r'}"
  done < <(grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' .env | sed -E 's/^[[:space:]]+//')
fi
export PYTHONIOENCODING=utf-8

if [[ -z "$SPLITS" ]]; then  # todos os splits presentes nos casos, na ordem em que aparecem
  SPLITS="$("$PY" -c "import json,pathlib; s=[]; [s.append(c['split']) for p in ['evals/cases.jsonl', *sorted(map(str, pathlib.Path('evals').glob('cases.d/*.jsonl'))), 'evals/heldout_blind.jsonl'] if pathlib.Path(p).exists() for c in map(json.loads, filter(str.strip, open(p, encoding='utf-8'))) if c['split'] not in s]; print(','.join(s))")"
fi
IFS=',' read -r -a LIST <<< "$SPLITS"
CLEAN=()
for s in "${LIST[@]}"; do s="${s// /}"; [[ -n "$s" ]] && CLEAN+=("$s"); done

if [[ $DRY -eq 1 ]]; then
  JUDGE=$([[ $NO_JUDGE -eq 1 ]] && echo False || echo True)
  echo "DRYRUN splits=$(IFS='|'; echo "${CLEAN[*]}") teto=$MAX_USD workers=$WORKERS repeat=$REPEAT juiz=$JUDGE processos=1"
  exit 0
fi

# Getnet v4 (01/11/2026): em fila, cada split herdava o que sobrou do anterior; memory e approval abortaram por teto
# (e o aborto SOBRESCREVEU um approval completo) e o juiz ficou sem nada. Por isso cada split tem a sua cota (80% do
# teto dividido igualmente) e o juiz os 20% restantes. Custo medido na v4 (repeat 3, Sonnet): official 0,85 · replan
# 0,88 · parallel 0,72 · approval 0,59 · memory 1,46 · juiz (90 respostas, Opus) 1,16 → ~6,1.
# Kit v5.1 (ensaio): os splits rodam ao mesmo tempo num processo SÓ (run_evals --splits). Com o buscador denso cada
# processo carrega e5-large + cross-encoder (GBs de RAM); um processo por split (5 ou mais) estourava a memória da
# máquina. Num processo, os modelos carregam uma vez e as threads dos splits os compartilham.
splits_usd="$("$PY" -c "print(round(float('$MAX_USD') * 0.8, 4))")"
share="$("$PY" -c "print(round(float('$MAX_USD') * 0.8 / ${#CLEAN[@]}, 4))")"
judge_usd="$("$PY" -c "print(round(float('$MAX_USD') * 0.2, 4))")"
mkdir -p var
JOINED="$(IFS=','; echo "${CLEAN[*]}")"
echo "== splits $JOINED num processo (cota US\$ $share cada) → var/live_splits.log"
set +e
"$PY" -m evals.run_evals --live --splits "$JOINED" --max-usd "$splits_usd" --workers "$WORKERS" --repeat "$REPEAT" \
  > var/live_splits.log 2>&1
code=$?
set -e
if [[ $code -eq 2 ]]; then echo "Sem credencial: na nuvem, APP_ANTHROPIC_API_KEY nas variáveis do ambiente; no PC, ANTHROPIC_API_KEY no .env."; exit 2; fi
failed=0
for split in "${CLEAN[@]}"; do
  status="$("$PY" -c "import json; print(json.load(open('evals/results/live_$split.json', encoding='utf-8')).get('status'))" 2>/dev/null || echo ausente)"
  echo "   $split: $status"
  [[ "$status" == "complete" ]] || failed=1
done
if [[ $code -ne 0 ]]; then  # 3 = algum split abortado (teto) ou DEGRADADO: o arquivo bom antigo dele, se houver, ficou intacto
  echo "   saída $code (split abortado, degradado ou quebrado) — veja var/live_splits.log; a rodada ruim NÃO substituiu o resultado anterior"
  failed=1
fi
[[ $failed -eq 0 ]] || echo "ATENÇÃO: split sem status complete (teto curto?). Rode de novo só ele: python -m evals.run_evals --live --split <s> --max-usd 2 --repeat $REPEAT"

if [[ $NO_JUDGE -eq 0 ]]; then  # juiz nos splits que mais pesam (official + replan); --judge-all para todos
  files=(); for s in official replan; do [[ -f "evals/results/live_$s.json" ]] && files+=("evals/results/live_$s.json"); done
  LLM_PROVIDER=anthropic "$PY" -m evals.judge "${files[@]}" --max-usd "$judge_usd"
fi
LLM_PROVIDER=offline "$PY" -m evals.run_evals > /dev/null  # relatório offline (bloco principal do README e gate)
"$PY" scripts/fill_readme.py
