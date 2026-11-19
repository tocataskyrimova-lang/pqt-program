# P8-G0 — Causal Weight Grafting and Capacity Expansion
## Поиск минимального механизма добавления доказуемой функции

**Проект:** `C:\PQT\P8_F3A_Q08`  
**База:** Qwen3.5-0.8B, 24 language layers  
**Режим:** development  
**Главная цель:** добавить модели новую способность минимальным числом новых параметров, доказать причинную роль graft и затем квантовать сам graft вплоть до ternary/Q1 там, где сохраняется устойчивость.

---

## 1. Центральная гипотеза

Модель можно улучшать не полным дообучением всех весов и не слепым копированием слоёв, а добавлением отдельной функциональной ткани:

`h' = h + α·Gθ(h)`

где база полностью заморожена, `Gθ` — новый graft, а `α=0` при инициализации, поэтому стартовая функция модели не меняется.

На G0 причинность доказывается сначала на уровне module/rank/channel/block. Доказательство функции каждого отдельного скаляра — более поздний уровень.

---

## 2. Как обучать при квантованной базе

Не оптимизировать packed GGUF, Q1/Q4 bitstream или отдельные дискретные биты напрямую.

Использовать:

```text
замороженная квантованная база
+
обучаемые FP16 shadow weights graft
+
fake quantization graft в forward
+
STE/QAT backward
+
экспорт финального graft в целевой формат
```

Базу можно держать в 8-bit или 4-bit; её веса не обновляются. Graft обучается через FP16/BF16 master weights, а forward постепенно ограничивается INT8/6/4, ternary или Q1.

---

## 3. Новая контролируемая способность

Создать формальный язык `KALPA-DSL`, сгенерированный после фиксации модели:

- 8 случайно названных операторов;
- преобразования строк, чисел и символических списков;
- композиции длиной 1–8;
- RU и EN формулировки;
- точный программный verifier.

Разделение:

```text
TRAIN: программы длиной 1–4
V1:    длина 1–4
V2:    длина 3–5
AUDIT: длина 5–8, новые композиции
```

Дополнительно использовать retention bank: RU/EN, code, math, JSON, instruction following и длинные ответы.

---

## 4. Турнир механизмов graft

### M1 — LoRA-Graft

Параллельный low-rank update:

`W' = W + BA`

База frozen. Это промышленный baseline.

### M2 — Zero-Gated Residual Graft

Основной кандидат:

`G(h) = U·φ(D·LN(h))`

`h' = h + tanh(g)·G(h)`

- `U` или gate инициализируется нулём;
- bottleneck width задаёт parameter budget;
- insertion sweep: после layers 7, 15 и 23;
- легко REMOVE, HOLD, REAP и вынести на другую GPU.

### M3 — Zero-Gated Macro-Block Expansion

Добавить один архитектурно совместимый Transformer macro-block:

- инициализация из близкого существующего block pattern;
- residual gate стартует с нуля;
- старые 24 слоя frozen;
- обучается только новый block и gate.

Это baseline настоящего depth expansion.

---

## 5. Справедливое сравнение

### Малый бюджет

`2–4M` новых параметров: M1 против M2.

### Средний бюджет

`8–16M` новых параметров: M1 против M2.

### Macro-block

M3 оценивать по:

- utility на миллион параметров;
- utility на дополнительный MiB;
- utility на потерю tok/s.

Все механизмы получают одинаковые данные, token budget, optimizer steps, retention loss и stopping rule.

---

## 6. Loss

Обучаются только graft weights:

`L = L_KALPA + λ1·L_base_logits + λ2·L_hidden + λ3·L_gate`

- `L_KALPA` — новая способность;
- `L_base_logits` — distillation исходной модели;
- `L_hidden` — ограничение representation drift;
- `L_gate` — штраф за избыточную амплитуду graft.

---

## 7. Экспериментальная лестница

### G0-A — Baseline

Измерить base model на KALPA, retention, скорость и память.

### G0-B — Mechanism Tournament

Обучить M1/M2/M3 и выбрать winner по Pareto:

1. KALPA V2;
2. retention;
3. worst-case stability;
4. число параметров;
5. latency;
6. пригодность к отдельному размещению и квантованию.

Audit не использовать до выбора winner.

### G0-C — Causal Proof

Для winner:

```text
ON       — graft включён
REMOVE   — gate=0 / graft удалён
SHAM     — random graft того же размера
SHUFFLE  — перестановка каналов/blocks
SCALE    — gate 0.0 / 0.25 / 0.5 / 0.75 / 1.0
```

Требование: новая способность исчезает при REMOVE, SHAM её не воспроизводит, utility связана с активностью graft.

`HOLD` здесь означает, что база frozen весь training и приобретённая способность обязана находиться в graft.

### G0-D — Internal REAP

Сокращать ranks, bottleneck channels, heads, sublayers и insertion points. После каждого шага разрешено короткое recovery training.

### G0-E — Quantized-Base Replication

Повторить winner при frozen base:

```text
INT8
NF4/4-bit, если backend корректно поддерживает архитектуру
```

Graft сначала остаётся FP16.

### G0-F — Graft QAT Ladder

Для минимального causal core:

```text
FP16
INT8
INT6
INT4
TERNARY {-1,0,+1}
Q1/BINARY {-1,+1}
```

Использовать shadow FP16 weights, fake quantization и STE. Разрешён progressive schedule:

`FP16 → INT8 → INT6 → INT4 → ternary → Q1`

Q1 не является обязательным успехом.

---

## 8. RTX 3060 + Tesla M40

Первичную разработку вести только на RTX 3060.

После выбора winner проверить:

```text
P0: base + graft на RTX 3060
P1: base на RTX 3060, graft на Tesla M40
P2: contiguous tail blocks + graft на M40
```

M40 использует FP16, не BF16. Допускается максимум 1–2 меж-GPU boundaries. Измерить tok/s, VRAM обеих карт и transfer bytes/token.

Цель: основная модель живёт на главной GPU, а добавленная способность — как подключаемый вычислительный орган на Tesla.

---

## 9. Статусы

### G0_MECHANISM_FOUND

- winner превосходит base на KALPA;
- retention damage проходит floors;
- REMOVE уничтожает новую способность;
- SHAM не проходит;
- winner Pareto-эффективнее альтернатив.

### G0_MINIMAL_CAUSAL_GRAFT

- REAP завершён;
- удаление следующего элемента нарушает gates.

### G0_QUANTIZED_GRAFT_READY

- frozen quantized base работает;
- graft проходит минимум INT4;
- качество и устойчивость сохранены.

### G0_EXTREME_LOWBIT_GRAFT_READY

- ternary или Q1 graft проходит все gates;
- long-horizon failure rate не растёт;
- используется реальный low-bit format/kernel.

Другие статусы:

```text
G0_NO_NEW_CAPABILITY
G0_RETENTION_FAILURE
G0_NO_CAUSAL_LOCALIZATION
G0_QUANTIZED_BASE_INCOMPATIBLE
G0_QAT_INSTABILITY
G0_Q1_STABILITY_FAILURE
BLOCKED_RUNTIME
```

---

## 10. Минимальные outputs

```text
configs\g0_config.json
configs\g0_kalpa_manifest.json

src\p8_f3a_q08\g0\
  kalpa_dsl.py
  graft_lora.py
  graft_residual.py
  graft_block.py
  qat.py
  train.py
  evaluate.py
  reap.py
  placement.py

outputs\g0\
  STATUS.json
  mechanism_comparison.csv
  causal_interventions.csv
  reap_trace.csv
  quantized_base_results.csv
  qat_ladder.csv
  placement_results.csv
  GRAFT_MANIFEST.json
  g0_summary.json

artifacts\g0\
  winning_graft\
  minimal_graft\
  quantized_graft\

docs\P8_G0_CAUSAL_WEIGHT_GRAFTING_REPORT.md
```

Не создавать audit ZIP и повторные копии base model.

---

## 11. Финальный отчёт Codex

```text
P8-G0 STATUS:

New skill:
Base score:
Winning mechanism:
Insertion point:
Added parameters:
Added size:
KALPA V2:
KALPA AUDIT:
Retention:
REMOVE:
SHAM:
Minimal graft parameters:
Best graft quantization:
Q1/ternary result:
Quantized base result:
RTX-only speed:
RTX+M40 speed:
Main conclusion:
```

После G0 остановиться. Не масштабировать автоматически.
