# QCatFormal — provenance package (QLP-06)

**Дата:** 2026-11-07, итерация после `QCAT-LEAN-PARITY-AUDIT-001` (`BOUNDED_ACCEPT / GLOBAL_HOLD`).
**Исполнитель:** Хикс. **Назначение:** снять замечание «в архиве указан `QMath_v3.md`, но сам файл и SHA-256 именно этой версии отсутствуют» и сделать внешнюю сборку воспроизводимой.

## 1. Снапшоты первоисточников

| Файл в `provenance/` | Исходный путь | SHA-256 | Байт | Строк |
|---|---|---|---|---|
| `QMath_v3.md` | `PQT-AUDIT-001/PQT-007/ASTRA_SIGMA_DERIVATION_2026-11-02_v001/sources/QMath_v3.md` | `144895e4ddd49ce01d71f8d69ce2e5b36f47d1a2d57d3e90155568650d7d252b` | 6502 | 649 |
| `Q-Mathematics_v3.md` | `PQT/Q-Mathematics v3.md` | `144895e4ddd49ce01d71f8d69ce2e5b36f47d1a2d57d3e90155568650d7d252b` | 6502 | 649 |
| `Q-Mathematics_v3.4_Canonical_PATCHED.md` | `PQT/REV/FROM_DOWNLOADS/Q-Mathematics_v3.4_Canonical_PATCHED.md` | `f9d9373c7527956426f4675f6fcb48f78a77d47ab8d5929de2b811c15bbf8f9e` | 20427 | 315 |

**Ключевой результат QLP-06:** `QMath_v3.md` и «найденный в Библиотеке» `Q-Mathematics v3.md`
**побайтово идентичны** (совпадают размер, число строк и SHA-256). Различны только даты
файлов в ФС (2026-11-02 и 2026-05-16) и имена. Таким образом неопределённость
«какая версия исторического текста имелась в виду» снята: это один и тот же документ.
Машинно читаемая копия хэшей — `SOURCE_HASHES.sha256`.

## 2. Line map: `QMath_v3.md` (исторический текст, 649 строк)

Файл имеет «колоночную» вёрстку: формулы разбиты на отдельные строки, поэтому
номера строк ниже — это **якоря фрагментов**, а не одной строки формулы.

| Строки | Содержание | Связь с Lean |
|---|---|---|
| 7 | `QCat=(Ob,Hom,⊗,I,β)` | не формализовано как `Category` (`not_claimed`) |
| 36–44 | объекты `Ob(QCat)=ℕ₀`, `m ⊗ n := m+n`, `I = 0` | не формализовано |
| 70–100 | `σᵢ(xᵢ,xᵢ₊₁) = ω(xᵢ,xᵢ₊₁)(xᵢ₊₁,xᵢ)` | `Historical.sigma12`, `sigma23` |
| 102 | `ω : Σ × Σ → Q₋₁ˣ` | `Historical.PhaseTable`; см. QLP-01 про `scope_of_wire` |
| 116–132 | **(B1) Local commutativity**, `σᵢσⱼ = σⱼσᵢ` при `\|i−j\|>1` | `BraidRelations.local_commutativity_B1` (σ₁/σ₃), `GeneralBraid.local_commutativity_general` |
| 136–160 | **(B2) Yang–Baxter relation**, `σᵢσᵢ₊₁σᵢ = σᵢ₊₁σᵢσᵢ₊₁` | `Historical.yang_baxter` (B2, не B1) |
| 168–190 | следствия для симметричности | `Historical.symmetric_iff_unit_monodromy` |
| 296–345 | §7 `δ`-braiding sector, `δ ⊗ δ`, `μ_δ` well-defined | не формализовано |
| 346–421 | §7.2 `δ` centrality (optional) | не формализовано |
| 425–490 | §9 compatibility with `μδ` | не формализовано |
| 520–549 | «только δ-sector symmetric», `δ` как коммутативный идемпотентный алгебра-объект | не формализовано |

**Важно:** нумерация B1/B2 исправлена в этой итерации. Раньше YBE ошибочно
называли B1; по первоисточнику B1 = локальная коммутативность, B2 = Янг–Бакстер.

## 3. Line map: `Q-Mathematics_v3.4_Canonical_PATCHED.md` (315 строк)

| Строка | Содержание |
|---|---|
| 13 | `Σ := {α, β, γ, δ}; 𝒞 := Σ³ (64 codons); Qσ := ℝ ⊕ ι, ι² = −σ; δ — Tamas/memory idempotent in Q₋₁, δ² = δ; QCat — strict monoidal category of codon rewrite rules; T: Id ⇒ (− ⊗ δ), μδ(δ⊗δ) = δ; Freeze_S(f) = S·id + (1−S)·f; Witness comonad W X := (X, ω).` |
| 15 | Witness principle (Постулат 0) |
| 31 | WitnessRegistry |
| 285 | naming rule (Sanskrit ↔ ASCII) |

Именно строка 13 фиксирует расхождение уровней `Σ` (4) и `𝒞 = Σ³` (64), которое
формализовано в `Scope.lean` / QLP-01. Отметим: в каноне `δ` объявлен идемпотентом
в `Q₋₁`, а `ι² = −σ` при `σ = −1` даёт `ι² = 1`, т.е. `ι` сам **не** идемпотент.
В `QAlgebra.lean` комментарий про «канон выбирает `δ = 1`» исправлен (QLP-04):
классификация даёт 4 идемпотента `{0,1,e₊,e₋}`, а выбор `δ` — внешняя конвенция.

## 4. Офлайн-зависимости

- `lean-toolchain`: `leanprover/lean4:v4.18.0` (Lean 4.18.0, Lake `5.0.0-11ccbce`).
- Mathlib: локальный path-зависимый офлайн-снимок `../mathlib-v4.18.0`, собранный
  по GitHub tree API с тега `v4.18.0`. Полное дерево: 6639 blob'ов, 7596 записей,
  `truncated=false`; 713 отсутствовавших файлов докачаны отдельно.
- 8 вспомогательных пакетов в `C:/AGI/qcat-lean-deps/`: `Cli`, `LeanSearchClient`,
  `Qq`, `aesop`, `batteries`, `importGraph`, `plausible`, `proofwidgets`
  (вместе с `mathlib` — 9 path-зависимостей в `lake-manifest.json`).
- **Git-метаданных нет**: снимки собраны из tree API, поэтому внешнего commit hash
  не существует. Вместо него — пофайловый манифест `DEPENDENCY_FILES.sha256`
  (**7149 файлов**: `.lean`, `.toml`, `.json`, `.js`, `lean-toolchain`), который
  однозначно фиксирует исходный набор. Локальные правки конфигов (path-зависимости,
  отключённый `widgetJsAll`, JS-стабы) также попадают в манифест.
- Деревья (`mathlib-v4.18.0` 423 МБ, `qcat-lean-deps` 80 МБ) **не** упакованы в ZIP
  из-за объёма; они идентифицируются манифестом. Для полностью автономной внешней
  сборки их нужно передать отдельно или сверить с официальным тегом `v4.18.0`.

## 5. Сборка

Полные логи в `provenance/build-logs/` (10 файлов):

- `qcat_lake_build.log` … `qcat_lake_build6.log` — последовательность отладки
  офлайн-сборки (npm/ProofWidgets, `include_str`, ошибки `Historical`/`MathlibBridge`/
  `QAlgebra`/`Naturality`/`RMap`).
- `qcat_lake_build6.log` — **первая успешная полная сборка** `QCatFormal`
  (`LAKE_BUILD_EXIT=0`, `Build completed successfully`).
- `qcat_final_check.log` — контрольная пересборка `QCatFormal`, exit 0.
- `qcat_kernel_build.log`, `qcat_kernel_final.log` — независимый проект
  `QCatFormal-Kernel` (только ядро Lean + `Std`), exit 0.
- `qcat_rmap_check.log` — точечная перепроверка `RMap.lean`.

Команда воспроизведения (из `C:/AGI/QCatFormal`):

```text
MATHLIB_NO_CACHE_ON_UPDATE=1 lake build
```

Флаг обязателен: `post_update`-хук Mathlib иначе пытается скачать `.olean` из
центрального кэша и падает в офлайне.

## 6. Что **не** заявлено

Первоисточники подтверждены и захэшированы, но это **не** означает, что Lean-проект
реализует всю QCat. `BraidedCategory QCat`, объекты `d`/`T`/`μ_d`, комонада Witness,
`Freeze`, `QCat₂L` и физические/PTR-утверждения остаются `not_claimed`.

## 7. Результат итерации QLP-01…06

| QLP | Артефакт | Статус |
|---|---|---|
| QLP-01 | `Scope.lean`: `WireScope`, `WireType`, `LiftPolicy`, `PhaseTable`, `codonFirst`/`codonLast`, `codon_scope_undetermined`, `lift_policy_not_determined`; `Historical.scope_of_wire = glyph` | выполнено |
| QLP-02 | `FreeModule.lean`: `σ₁₂`, `σ₂₃` как `LinearMap` на `Triple →₀ K` через `Finsupp.lsum`; `yang_baxter` на всём модуле через `Finsupp.induction_linear` | выполнено |
| QLP-03 | `Comparison.lean`: `braid_label_actions_differ` (переименование), `NaturalRewrite`, `natural_rewrite_classes_differ` | выполнено |
| QLP-04 | `QAlgebra.lean` комментарии исправлены; `Qm1NBad.lean`: Q₋₁-native контрмодель (фазы `1`/`−1`, монодромия `−1`) | выполнено |
| QLP-05 | `Naturality.lean`: `scalar_zero_image_counterexample`, `not_claimed(N1)`, `not_claimed(T0)` | выполнено |
| QLP-06 | этот пакет: снапшоты, `SOURCE_HASHES.sha256`, `DEPENDENCY_FILES.sha256`, `build-logs/`, `BUILD_SUMMARY.md` | выполнено |
| доп. | `GeneralBraid.lean`: B1 для всех `n` и непересекающихся позиций, B2 для всех `n` | выполнено |

**Ключевая находка QLP-06:** `QMath_v3.md` и `Q-Mathematics v3.md` — один и тот же
файл (SHA-256 `144895e4…d7d252b`). Различаются только имена и даты в ФС.

**Ключевая техническая находка:** при точечных импортах у `ℝ × ℝ` **не было**
`CommRing`/`CommMonoid` — только `Prod.instMul` и `Prod.instOne`. Прежний
комментарий `QAlgebra.lean` о «буквально `CommRing (ℝ × ℝ)` из Mathlib» был
неточен; исправлено добавлением `Mathlib.Algebra.Ring.Prod`.

## 8. Снапшоты

| Файл | Содержимое | SHA-256 |
|---|---|---|
| `QCatFormal-SNAPSHOT-PRE-QLP-2026-11-07.zip` (в `C:/AGI`) | состояние **до** правок QLP: оба проекта + provenance | в файле `QCatFormal-SNAPSHOT-PRE-QLP-2026-11-07.zip.sha256` |
| `QCatFormal-SNAPSHOT-QLP-2026-11-07.zip` (в `C:/AGI`) | состояние **после** QLP-01…06: оба проекта + provenance | в файле `QCatFormal-SNAPSHOT-QLP-2026-11-07.zip.sha256` |

Хэши вынесены в отдельные `.sha256`-файлы рядом с архивами, чтобы не возникало
циклической зависимости (хэш архива не может быть записан внутрь самого архива).

ZIP-архивы содержат исходники, конфигурацию и provenance, но **не** содержат
деревья `mathlib-v4.18.0` (423 МБ) и `qcat-lean-deps` (80 МБ); их фиксирует
пофайловый манифест `DEPENDENCY_FILES.sha256` (7149 файлов).
