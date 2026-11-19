# QCat-CatBridge — QCAT-CAT-BRIDGE-001

Мост: **QCat-008 → конечная стохастическая динамика → наблюдатель с
first-return trace**. Дополнения **ADDENDUM-002** (H1, H2, H3) и
**ADDENDUM-003** (исправленный Tower Law) — в том же каталоге, базовая линия
не тронута.

Lean 4.18.0 (commit `11ccbced7964`) · Lake 5.0.0-11ccbce ·
Mathlib v4.18.0 (path-зависимость `../mathlib-v4.18.0`).
Базовая линия `QCat-BraidCore-SNAPSHOT-008` **не изменялась**
(`9003fae29feb9a8895c31fdd92174c978e79a2be565cef210a8fcce05dc1c745`).

## Сборка

```bash
cd C:\AGI\QCat-CatBridge
set MATHLIB_NO_CACHE_ON_UPDATE=1
lake build
```

Ожидаемо: `Build completed successfully`, `1101/1102`, `exit 0`, `sorryAx = 0`.

## Сертификация (ADDENDUM-003, прогон 2026-11-08)

| Метрика | Значение |
|---|---|
| цели сборки | 1101 / 1102 (последняя — корневой таргет) |
| exit code | `0` |
| ошибки | 0 |
| `sorryAx` | 0 |
| `sorry` / `admit` / `unsafe` / `axiom` в исходниках | 0 |
| директив `#print axioms` | 101 |
| множества аксиом | `{propext, Classical.choice, Quot.sound}` (100) · `{propext}` (1) |

Единственная теорема с `{propext}` — `lossy_cannot_recover` (доказана `rw`,
без классики). Пользовательских аксиом нет.

Логи: `provenance/build-logs/build-bridge-001.log` (M1–M4),
`provenance/build-logs/build-bridge-002.log` (M1–M4 + H1 + H2),
`provenance/build-logs/build-bridge-003.log` (M1–M4 + H1 + H2 + ADDENDUM-003).

## Модули

| Файл | Содержание |
|---|---|
| `QCatCatBridge/MarkovKernel.lean` | `StochMatrix` над ℚ, замыкание по умножению, единица, `Glyph = Fin 4`, 12 внедиагональных пар, ядро `Q_w`, фикстуры `Q4`/`QNU`, **обструкция** «стохастичность ⇒ `ω = 1`» (в узкой области) |
| `QCatCatBridge/ObserverTrace.lean` | блоки `A B C D`, `Tr_V = A + B(I−D)⁻¹C` только при сертифицированном `Dinv`, неотрицательность, суммы строк, ряд Неймана как тождество с остатком, граница `D = I`, точные `Q_RGB` и `Q4` |
| `QCatCatBridge/TraceComposition.lean` | контрпример `Tr(P·R) ≠ Tr(P)·Tr(R)` с явными матрицами, yanking для `[[0,I],[I,0]]` |
| `QCatCatBridge/TowerLaw.lean` | **ADDENDUM-003** — башня `Tr_{V2}(Tr_{V1}(Q)) = Tr_{V2}(Q)` с тремя сертифицированными обратными; прямоугольные блоки `rowBlock`/`colBlock`, `schurInv`, `tower_schur`, `tower_traceV`, контрольная точка `c_*` |
| `QCatCatBridge/PhaseObservation.lean` | `R = ℚ×ℚ`, `e₊/e₋/ι`, критерий видимости, слепота `e₊`, немультипликативность `Π_λ`, выпуклые смеси, **H1** — точный дефект проекции |
| `QCatCatBridge/SignRealization.lean` | **H2** — `M(g) = [[p_stay,p_flip],[p_flip,p_stay]]`, неверная (nonfaithful) реализация `{±1}²` |
| `QCatCatBridge/Audit.lean` | 101 директива `#print axioms` |

## Главные результаты

**Обструкция M1 (NO_GO, узкая область).** `stochastic_phase_forces_one`: если
`ω·swap` стохастическая, то `ω = 1`. Это утверждение о **прямой** реализации
«скалярный вес × перестановка». Скрытые состояния, нелинейные отображения и
неверные наблюдательные отображения теоремой **не** исключаются — см.
`SignRealization.lean` как явный контрпример к «универсальности».

**След M2 (MC-C).** `traceV` принимает `Dinv` **явно**; без сертифицированного
обратного резольвентной формулы нет. `absorbing_no_inverse` доказывает, что при
`D = I` обратного нет вовсе, а `absorbing_gives_substochastic` — что наивный
след субстохастичен и не подлежит молчаливой нормировке. Отсутствие обратного
не отменяет само событие первого возвращения — оно делает недоступной именно
эту формулу.

**Точные фикстуры (MC).**
`QRGB_trace`: `[[19/45, 26/45], [61/90, 29/90]]`.
`Q4T_trace`: все элементы `1/3`.

**Нефункториальность M3 (NO_GO).** `Tr(P) = Tr(R) = I₂`, но
`Tr(P·R) = swap₂`. Явные значения, не булево «не равно».

**Tower Law M3 (MC-C, ADDENDUM-003).** `tower_schur`:
`A11 + [A12,B1]·(I−[[A22,B2],[C2,D]])⁻¹·[A21;C1]
 = A11 + B1 Dinv C1 + (A12 + B1 Dinv C2)·Sinv·(A21 + B2 Dinv C1)`
при трёх явных сертификатах: `Dinv·(I−D) = 1`,
`Sinv·(I − (A22 + B2 Dinv C2)) = 1`, `(I−M)·Tinv = 1`.
`tower_traceV` переносит это на уровень `traceV`: двойной след по `H`, затем
по `W`, равен одному следу по `W ⊕ H`. Контрольная точка аддендума
`Q = [[1/4,1/2,1/4],[1/3,1/3,1/3],[1/2,0,1/2]]` даёт `1` (`c_tower`);
ошибочная формула без `I −` дала бы `1/2` (`c_wrong_value`).

**Фаза M4 (MC).** `eplus_blind`: при `u = e₊`, `ω₁ = 1`, `ω₂ = ι` выходы
совпадают при любом `λ`. `Pi_not_multiplicative`: `Π_λ` не мультипликативна
при `0 < λ < 1`.

**H1 (MC).** `Pi_defect`: `Π_λ(z·w) − Π_λ(z)Π_λ(w) =
λ(1−λ)(z₊−z₋)(w₊−w₋)` — без гипотез. `Pi_multiplicative_iff`:
мультипликативность на всей `ℚ×ℚ` ⇔ `λ ∈ {0,1}`. `mulSC_injective_iff`:
умножение на `u` инъективно ⇔ `u₊ ≠ 0 ∧ u₋ ≠ 0`.

**H2 (MC).** `M(g)` стохастическая и перестановочная, `M(1,1) = I₂`,
`M(1,−1) = swap₂`, `M(g·h) = M(g)M(h)`, `ker M = {(1,1), (−1,−1)}`
(`Mmat_kernel_at_one`, `Mmat_global_sign_blind`, `Mmat_not_injective`).
Сводный сертификат — `sign_realization_summary`.

## Что НЕ заявлено

- Traced-моноидальная структура (JSV) — yanking сам по себе её не даёт, и
  доказанная башня её тоже не даёт: одно тождество для одного разбиения ≠
  аксиомы dinaturality / vanishing I,II / superposing.
- Tower Law доказан **при явных сертификатах** `Dinv`, `Sinv`, `Tinv`.
  Существование этих обратных (то есть когда `I − D`, `I − S22`, `I − M`
  обратимы) не выводится — оно предъявляется свидетелем.
- `MonoidalFunctor` QCat → Stoch — не построен, есть обструкция.
- Несимметрическая фазовая категория — отдельная трасса `QCAT-DAGGER-GATE-009`.
- Физическое время, лоренцевские утверждения, скорость `c`, предсказания
  частиц, сознание — не заявлялись.
- `e₋` как «стерильный физический сектор», отрицательные фазы как вероятности,
  отображение «фаза → вероятность» — не вводились.
- H2 **не** является правилом Борна и **не** является контрпримером к
  `stochastic_phase_forces_one`: это намеренно неверная реализация.

## Independent replay (для Codex)

```bash
# 1. распаковать снапшот в чистый каталог (рядом должен лежать Mathlib v4.18.0)
unzip QCat-CatBridge-SNAPSHOT-BRIDGE-003-2026-11-08.zip -d QCat-CatBridge
# 2. проверить, что Mathlib — ровно тот commit, и что ../mathlib-v4.18.0 существует
cat QCat-CatBridge/lean-toolchain        # leanprover/lean4:v4.18.0
# 3. собрать без изменения сторонних кешей
cd QCat-CatBridge
export MATHLIB_NO_CACHE_ON_UPDATE=1
lake build; echo "EXIT=$?"               # ожидается EXIT=0
# 4. повторный аудит аксиом (вывод в stdout, ничего не пишется в Mathlib)
lake env lean QCatCatBridge/Audit.lean | grep "depends on axioms" | sort | uniq -c
#    ожидается: 100 x [propext, Classical.choice, Quot.sound], 1 x [propext]
# 5. проверка отсутствия заглушек
grep -rnE "\b(sorry|admit|unsafe)\b|^axiom " QCatCatBridge/*.lean
#    ожидается ровно одна строка: QCatCatBridge/Audit.lean:6 — это docstring,
#    а не код; в телах доказательств совпадений нет
```

Шаг 4 не требует пересборки Mathlib и не пишет в его кеш. Хеши артефактов —
`provenance/SOURCE_HASHES.sha256`; хеш снапшота — в файле
`SNAPSHOT_BRIDGE-003.sha256` рядом с архивом (внутрь архива он не кладётся:
хеш архива не может содержаться в нём самом).

Карта соответствия источник → теорема → гипотезы → вердикт:
`CORRESPONDENCE.md`.
