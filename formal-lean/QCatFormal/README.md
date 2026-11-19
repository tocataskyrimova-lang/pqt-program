# QCatFormal — машинно проверяемое ядро QCat

Lean **4.18.0** + Mathlib **v4.18.0** (офлайн-снимок `../mathlib-v4.18.0`),
Lake `5.0.0-11ccbce`, elan `4.2.3`. Версии **зафиксированы совместно**:
`lean-toolchain` и Mathlib-снимок смотрят на один и тот же тег `v4.18.0`.
Существующие проекты не изменялись: всё лежит в новых каталогах
`QCatFormal/`, `QCatFormal-Kernel/`, `mathlib-v4.18.0/`, `qcat-lean-deps/`.

Текущая итерация — реакция на `QCAT-LEAN-PARITY-AUDIT-001`
(`SOURCE_PARITY = PARTIAL_ACCEPT`, `GLOBAL_QCAT_CERTIFICATION = BLOCKED`):
выполнены QLP-01…QLP-06. Внешняя сертификация по-прежнему **не** выдана.

## Сборка

```bash
cd C:/AGI/QCatFormal
MATHLIB_NO_CACHE_ON_UPDATE=1 lake build
```

Флаг отключает mathlib'овский post-update хук `lake exe cache get`: снимок
офлайн, центральный кэш `.olean` не используется. Без флага хук падает.
`lake-manifest.json` содержит только `type: path` зависимости — сеть не нужна.

Независимое ядро (голый Lean + `Std`, без Mathlib) собирается отдельно и быстро:

```bash
cd C:/AGI/QCatFormal-Kernel
lake build
```

Аудит аксиом печатается прямо при сборке (`#print axioms` в `Audit.lean`,
`BraidRelations.lean`, `StdOnly.lean`, `Scope.lean`, `Comparison.lean`).
Ожидаемые аксиомы: `propext`, `Quot.sound`, `Classical.choice`,
`Lean.ofReduceBool` (последняя — от `native_decide`). `sorryAx` быть не должно.

## Что изменено в итерации QLP-01…06

| QLP | Требование аудита | Что сделано |
|---|---|---|
| **QLP-01** | зафиксировать `scope_of_wire ∈ {glyph,codon}` и подъём ω 4→64 | `Scope.lean`: `WireScope`, `WireType`, `LiftPolicy`, `PhaseTable` (с полем `scope` и доказанным согласием), `codonFirst`/`codonLast`, теорема `codon_scope_undetermined`. `Historical.scope_of_wire = glyph` — явно. |
| **QLP-02** | `Triple →₀ K`, K-линейные σᵢ, перенос по линейности | `FreeModule.lean`: `σ₁₂`, `σ₂₃` — `LinearMap` через `Finsupp.lsum`; YBE на мономе + `Finsupp.induction_linear` на всём модуле; `sigma12Lin_apply` показывает действие на произвольном элементе. |
| **QLP-03** | переименовать `rewrite_classes_differ`, ввести `NaturalRewrite` | `Comparison.lean`: теорема переименована в `braid_label_actions_differ`; добавлен `NaturalRewrite` (односторонняя естественность); доказано `natural_rewrite_classes_differ` (flip — все `f`, R — сдвиг на 1 нет). |
| **QLP-04** | исправить комментарии, Q₋₁-native N-bad | `QAlgebra.lean`: убрано ложное «монодромия −1 недостижима», исправлено «δ = 1». `Qm1NBad.lean`: отдельная контрмодель с фазами `1`/`−1`, без `√−1`. |
| **QLP-05** | `T0_admits_nonscalar_braiding` → `scalar_zero_image_counterexample`, `not_claimed(N1,T0)` | `Naturality.lean`: переименовано, границы выписаны явно; комплексная модель помечена как ℂ-модель, не Q₋₁. |
| **QLP-06** | снапшоты первоисточников, hash/line map, зависимости, build log | `provenance/`: `PROVENANCE.md`, `SOURCE_HASHES.sha256`, `DEPENDENCY_FILES.sha256` (7149 файлов), `build-logs/`, снапшот `QCatFormal-SNAPSHOT-PRE-QLP-2026-11-07.zip`. |

Дополнительно закрыт пункт «весь B1 для всех длин и позиций»:
`GeneralBraid.lean` доказывает B1 для произвольных непересекающихся позиций и
B2 (Yang–Baxter) для любых трёх различных позиций при любом `n`.

## Сертификация

| Проверка | Результат |
|---|---|
| `MATHLIB_NO_CACHE_ON_UPDATE=1 lake build` в `QCatFormal` | **PASS**, exit 0, 1215 целей, `Build completed successfully` (лог `provenance/build-logs/qcat_qlp_build.log`) |
| `lake build` в `QCatFormal-Kernel` | **PASS**, exit 0 (голый Lean + Std) |
| `#print axioms` | **60** записей; **3** теоремы не зависят ни от каких аксиом; 0 ошибок сборки |
| Множество аксиом | ровно `propext`, `Classical.choice`, `Quot.sound`, `Lean.ofReduceBool` |
| `sorryAx` | **отсутствует** (0 вхождений в логе сборки) |
| `sorry` / `admit` / `axiom` / `unsafe` в исходниках | **отсутствуют** (вхождения только в комментариях) |
| Версии | `lean-toolchain = leanprover/lean4:v4.18.0`, Mathlib `v4.18.0` через `path`-зависимость; 9 записей `type: path` в manifest |

Не влияющие на проверку ядром предупреждения: наследие офлайн-заглушек
`ProofWidgets` (хеши JS-модулей) и style-linter в `RMap.lean`.

## Карта модулей

| Файл | Слой | Что доказано |
|---|---|---|
| `Historical.lean` | Mathlib | **Первоисточник** `σᵢ(a,b)=ω(a,b)(b,a)`: B2/YBE для любой ω (обратимость не нужна); `σ²=id ⇔ ω(x,y)ω(y,x)=1`; несимметричность без смены меток; `scope_of_wire = glyph` (QLP-01) |
| `BraidRelations.lean` | Mathlib | **B1** на словах длины 4: `σ₁σ₃=σ₃σ₁` при любых фазах; при `[CommGroup K]` построен `σ⁻¹` |
| `GeneralBraid.lean` | Mathlib | **B1 для всех n и позиций** (непересекающиеся носители) и **B2 для всех n** (три различные позиции), любая ω в коммутативном моноиде |
| `FreeModule.lean` | Mathlib | **QLP-02:** `σ₁₂`, `σ₂₃` — `K`-линейные операторы на `Triple →₀ K`; YBE переносится с базиса на весь модуль через `Finsupp.induction_linear` |
| `Scope.lean` | Std | **QLP-01:** `WireScope` (`glyph`/`codon`), `PhaseTable` с явной областью, два лифтинга 4→64, `codon_scope_undetermined`: глифовая ω не определяет кодонную Ω |
| `Comparison.lean` | Std | **QLP-03:** `braid_label_actions_differ` (σ инволютивна, R порядка 64) и `natural_rewrite_classes_differ` (для flip естественно всё, для R — нет) |
| `StdOnly.lean` | Std | Диэдральная `R(a,b)=(b,2b−a)` на `Fin 64`: обратимость, YBE перебором, `Rᵏ`-формула, `R⁶⁴=id`, `R²≠id` |
| `QAlgebra.lean` | Mathlib | `Q₋₁ ≅ ℝ×ℝ`, `ι²=1`, `e±`, классификация идемпотентов `{0,1,e₊,e₋}`, отсутствие `√−1`; комментарии исправлены по QLP-04 |
| `Qm1NBad.lean` | Mathlib | **QLP-04:** Q₋₁-native N-bad: фазы `1`/`−1`, все обратимы, монодромия `−1` достижима, таблица не скалярна |
| `RMap.lean` | Mathlib | Символьная версия диэдральной R на `ZMod 64` |
| `Naturality.lean` | Mathlib | **QLP-05:** `scalar_zero_image_counterexample`; `not_claimed(N1)`, `not_claimed(T0)` |
| `MathlibBridge.lean` | Mathlib | `#check` доступности `BraidedCategory`, `braiding_naturality_left/right`, `braiding_naturality`, `hexagon_forward/reverse`, `yang_baxter` |
| `Audit.lean` | Mathlib | `#print axioms` по ключевым теоремам |
| `Basic.lean` | — | Маркер связки версий |

## Факты версии Mathlib v4.18.0, всплывшие при сборке

* Объединённая естественность брейдинга называется
  `CategoryTheory.BraidedCategory.braiding_naturality`
  (`Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean:118`), а **не**
  `CategoryTheory.braiding_naturality` — последнего имени в этой версии нет.
* **`ℝ × ℝ` не имеет `CommRing` без `Mathlib.Algebra.Ring.Prod`.** При точечных
  импортах были доступны только `Prod.instMul` и `Prod.instOne`; `#synth
  CommMonoid (ℝ × ℝ)` падал. Поэтому `QAlgebra.lean` и `Qm1NBad.lean` явно
  импортируют `Mathlib.Algebra.Ring.Prod`. Это исправление: прежний комментарий
  «буквально `CommRing (ℝ × ℝ)` из Mathlib» был неточен.
* У `ℝ × ℝ` нет `OfNat … 2` (нет `NatCast` для произведений) — есть только
  `0` и `1`. Поэтому `(1±ι)/2` выписано как деление на явную пару
  `((2 : ℝ), (2 : ℝ))`.
* `Real.instDivInvMonoid` невычислим: `re`/`im` объявлены в
  `noncomputable section`. Теоремы — `Prop`, на проверку ядром не влияет.
* `CommMonoid` отсутствует в `Std`: модули с алгебраической иерархией
  (`Historical`, `BraidRelations`, `GeneralBraid`, `FreeModule`) импортируют
  `Mathlib.Algebra.Group.Basic`.

## Явные границы (`not_claimed`)

* **Категорийный экземпляр `BraidedCategory QCat` не построен.** Нет
  `Category`/`MonoidalCategory` для QCat, тензора как функтора, гексагонов и
  естественности braiding. `MathlibBridge.lean` лишь проверяет доступность API.
* **Общая naturality для всех `r ∈ R_{m,n}` не доказана.** Доказана
  естественность для конкретного `flip` и отсутствие её для `R` со сдвигом;
  замороженный список `R_{m,n}` не формализован.
* **Теорема N1** (`M₄(ℂ)`, коммутант `M₁₆`, `R = rP`) не формализована.
* **Модель всей конечной презентации `T₀`** (12 генераторов, relations,
  функтор `F`, матрица `R` на `V⊗V`) не построена; `Naturality.lean` даёт
  скалярную контрольную модель, а не контрмодель `T₀`.
* **Объекты памяти `d`, `T`, `μ_d`, комонада Witness, `Freeze`, `QCat₂L`,
  физические/PTR-предсказания** — не формализованы.
* **Диэдральная R не является брейдингом первичного QCat.** Это независимая
  альтернативная модель.
* **Уровень области ω в первичных текстах не зафиксирован.** `Scope.lean`
  фиксирует выбор явно и доказывает, что лифтинг не определяется текстом.

## Сверка с первоисточниками

Снапшоты и хэши — в `provenance/`:

* `QMath_v3.md` — SHA-256 `144895e4…d7d252b`, 6502 байта, 649 строк;
* `Q-Mathematics v3.md` — **побайтово тот же файл** (тот же SHA-256), то есть
  неопределённость «какая версия исторического текста» снята;
* `Q-Mathematics_v3.4_Canonical_PATCHED.md` — SHA-256 `f9d9373c…5bbf8f9e`,
  20427 байт, 315 строк.

Line map ключевых мест `QMath_v3.md`: строка 7 — `QCat=(Ob,Hom,⊗,I,β)`;
70–100 — формула σᵢ; 102 — `ω : Σ×Σ → Q₋₁ˣ`; **116 — B1** (local
commutativity); **136 — B2** (Yang–Baxter); 296–345 — δ-сектор. В каноне v3.4
строка 13 задаёт `Σ`, `𝒞 := Σ³`, `Qσ`, `δ²=δ`, `T`, `μδ`, `Freeze_S`, Witness.

### Карта соответствия (подготовлено Хиксом, подпись Жеки требуется)

| Теорема в Lean | Формулировка в первоисточнике | Статус |
|---|---|---|
| `Historical.yang_baxter` | `QMath_v3.md` **B2** (строка 136) | доказано в модели «свободный базис + коммутативный `K`»; **модель**, не категорийная аксиома |
| `GeneralBraid.local_commutativity_general` | **B1** (строка 116), `\|i−j\|>1` | доказано для всех `n` и всех непересекающихся позиций |
| `GeneralBraid.yang_baxter_general` | **B2** (строка 136) | доказано для всех `n` и трёх различных позиций |
| `BraidRelations.sigma12Inv_sigma12` | обратный брейдинг из `Q₋₁ˣ` | доказано при `[CommGroup K]` |
| `FreeModule.yang_baxter` | B2 в линейной модели | доказано на всём `Triple →₀ K`, не только на мономах (QLP-02) |
| `Historical.symmetric_iff_unit_monodromy` | `σ² = id ⇔ ω(a,b)ω(b,a)=1` | доказано |
| `Scope.codon_scope_undetermined` | `ω : Σ×Σ` против `𝒞 := Σ³` | доказано, что уровень текстами не фиксируется (QLP-01) |
| `Comparison.braid_label_actions_differ` | сопоставление σ и `R(a,b)=(b,2b−a)` | доказано: действия на метках различны |
| `Comparison.natural_rewrite_classes_differ` | различие классов естественных переписываний | доказано для flip и R со сдвигом (QLP-03) |
| `QAlgebra.idempotents_classified` | `δ²=δ`, `e±` | доказано; **какой именно** идемпотент есть δ — не зафиксировано |
| `QAlgebra.no_sqrt_neg_one` | отсутствие `√−1` в Q₋₁ | доказано; **не** влечёт недостижимость монодромии −1 (QLP-04) |
| `Qm1NBad.Qm1_native_counterexample` | N-bad над `Q₋₁ˣ` | доказано: монодромия −1 достижима единицами `1`/`−1` |
| `Naturality.scalar_zero_image_counterexample` | §7 аудита: нужна гипотеза `F(r)≠0` | доказано логическое ядро; **N1/T₀ не заявлены** |
| `BraidedCategory` / гексагоны / `T` / `μδ` / `QCat₂L` | `QMath_v3.md`, канон v3.4 | **not_claimed** |

Из трёх условий приёмки выполнены два: **сборка** и **аудит аксиом**.
Третье — **сверка формулировок с первоисточниками Жекой** — не выполнено:
таблица выше проект для подписи, а не акт приёмки.
