# QCat-BraidCore

Конструктивное брайд-ядро QCat: категория, моноидальная структура, сплетение,
типизированный объектный слой и линейная фазовая картина — всё **без**
`axiom` и **без** `sorry`.

* Задание: `QCAT-CATEGORY-CLOSURE-007`.
* Итерация **008** — ответ на `QCAT_CLOSURE_007_ILORI_AUDIT` (F1–F4, §4).
* Карта соответствия источникам: [`CORRESPONDENCE.md`](CORRESPONDENCE.md).
* Связка версий: Lean `4.18.0`, Lake `5.0.0-11ccbce`, Mathlib `v4.18.0`
  (path-зависимость `../mathlib-v4.18.0`, офлайн-снимок).

---

## 1. Что доказано

| Слой | Lean-константа | Содержание |
|---|---|---|
| Категория | `BraidCore.instCategory` | `id`, `comp`, `id_comp`, `comp_id`, `assoc` |
| Моноидальность | `BraidCore.instMonoidalCategory` | `⊗ = Sum`, `𝟙_ = PEmpty`, пентагон, треугольник, 3 естественности |
| Сплетение | `BraidCore.instBraidedCategory` | `β_ = Equiv.sumComm`, обе естественности, оба шестиугольника |
| **Симметричность (F1)** | `BraidCore.instSymmetricCategory`, `braiding_double_eq_id` | `(β_ X Y).hom ≫ (β_ Y X).hom = 𝟙 (X ⊗ Y)` — **в типе класса**, а не в комментарии |
| **Единицы (F4)** | `BraidCore.phase_isUnit`, `isIso_of_isUnit_phase` | `BraidCore Kˣ` — точная фазовая модель; изоморфизмы `BraidCore K` = морфизмы единичной фазы |
| **Типизированный слой (F2/F3)** | `Typed.ColoredWord`, `Rewrite`, `Braid`, `modelOf`, `objectMap` | `Ob = Σ*`, `r_{y←x} : [x] ⟶ [y]`, `b_{x,y} : [x,y] ⟶ [y,x]` |
| Фазовая naturality | `PhaseNaturality.sigma_natural_left_iff` / `_right_iff` | квадрат коммутирует **⇔** `ω(f a,b)=ω(a,b)` |
| Постоянство фазы | `all_unary_implies_constant`, `constants_imply_constant`, `generators_imply_constant` | все унарные / константы / 12 генераторов ⇒ `ω` постоянна |
| **Линейная картина (§4)** | `LinearPhase.naturality_left_iff` / `_right_iff` | `u·(ω₁−ω₂) = 0` — точный критерий |
| **Условная теорема (§4)** | `all_units_imply_constant` | обратимость всех `u_yx` ⇒ `ω` постоянна |
| **Свидетель (§4)** | `zero_divisor_blocks_conclusion`, `distinct_phases_same_morphism` | `u = e₊ ≠ 0` **не** влечёт равенство фаз |
| Реестр | `Generators.card_rewriteGen`, `card_braidingGen` | 12 генераторов, 16 компонентов |

Ни одна когерентность не постулирована: все условия `MonoidalCategory`,
`BraidedCategory` и `SymmetricCategory` — теоремы, доказанные поточечно
(`ext` → разбор вариантов `Sum` → `rfl`).

## 2. Границы (после аудита Илори)

| Пункт аудита | Ответ | Где |
|---|---|---|
| **F1** «сплетение симметрично» | Подтверждено и поднято в тип: `instSymmetricCategory`. `BraidCore` — **симметрическая** модель; несимметрический фазовый braiding ею не представлен | `Braided.lean` |
| **F2** «уровни объектов различны» | Построен слой `Ob = Σ*`; связь с `BraidCore` — **изоморфизмы**, не равенства (`appendComparison`, `unitComparison`). `MonoidalFunctor` **не** объявлен | `ColoredWord.lean` |
| **F3** «`replace` ≠ типизированная стрелка» | Введён явный `modelOf`; доказано, что он уважает типизацию, **верен** (`modelOf_injective`) и не добавляет соотношений (`modelOf_comp_not_eq`) | `ColoredWord.lean` |
| **F4** «`phase : K` допускает 0» | `BraidCore K` — широкая оболочка; точная модель — `BraidCore Kˣ`; изоморфизмы = морфизмы единичной фазы | `Basic.lean` |
| **§4** «no-go не безусловен» | Подтверждено: `u·(ω₁−ω₂)=0` — точный критерий; при обратимом `u` — постоянство; при `u = e₊` — контрпример `1` vs `ι` | `LinearPhase.lean` |

## 3. Чего здесь НЕТ

* **Несимметрической фазовой категории.** `BraidCore` симметрична
  (F1). Историческая `ω` с `ω(a,b)ω(b,a) ≠ 1` в ней не представлена.
* **`MonoidalFunctor`** из словесной презентации в `BraidCore`:
  `(w ++ v).length = w.length + v.length` — теорема, а не `rfl`.
* **Полной T0**: память `δ`, `T`, `μ_δ`, `Witness`, dagger
  `r_{y←x}† = r_{x←y}`, `QCat₂L`.
* **Многоместной naturality** — есть только реестр и шаблон
  (`MultiPlacePhaseNatural`), проверки нет.
* **Согласованности свидетеля §4 с dagger/memory** — проверена только
  чистая фазово-переписывательная часть.
* **Физических следствий / PTR.**

## 4. Воспроизводимая сборка

```bash
cd C:\AGI\QCat-BraidCore
$env:MATHLIB_NO_CACHE_ON_UPDATE=1
lake build
```

Зафиксировано в `provenance/build-logs/build-008-2026-11-07.log`:

```
Build completed successfully.
targets:            898/898
errors:             0
sorryAx:            0
#print axioms:      58 директив
без аксиом:         7 теорем
множества аксиом:   {propext}
                    {propext, Quot.sound}
                    {propext, Classical.choice, Quot.sound}
```

Ни одного пользовательского `axiom`, ни одного `sorry`. `Classical.choice`
появляется только там, где участвуют `Fintype`/`decide`/`ℝ × ℝ`
(подсчёт мощностей и арифметика в свидетеле), а не в структурных теоремах.

## 5. Структура

```
QCat-BraidCore/
├── lakefile.toml                 # defaultTargets = QCatBraidCore + Audit
├── lean-toolchain                # leanprover/lean4:v4.18.0
├── QCatBraidCore.lean            # корневой модуль
├── README.md
├── CORRESPONDENCE.md             # карта: клауза → теорема → гипотезы → вердикт
├── QCatBraidCore/
│   ├── Basic.lean                # BraidCore, Hom, Category, BraidCore Kˣ
│   ├── Monoidal.lean             # ⊗, 𝟙_, MonoidalCategory
│   ├── Braided.lean              # β_, BraidedCategory, SymmetricCategory
│   ├── PhaseNaturality.lean      # критерий фазовой naturality (п.4–5)
│   ├── ColoredWord.lean          # Σ*, типизированные стрелки, modelOf (F2/F3)
│   ├── LinearPhase.lean          # линейное представление, Q₋₁-свидетель (§4)
│   ├── Generators.lean           # реестр 12 + 16 (п.6)
│   └── Audit.lean                # 58 × #print axioms
└── provenance/
    ├── SOURCE_HASHES.sha256
    └── build-logs/
        ├── build-full-2026-11-07.log   # итерация 007 (36 директив, 690 целей)
        └── build-008-2026-11-07.log    # итерация 008 (58 директив, 898 целей)
```

## 6. Версионные факты, на которые опирается код

* `MonoidalCategoryStruct.whiskerLeft`/`whiskerRight` имеют **неявные**
  `{Y₁ Y₂}` / `{X₁ X₂}`; в `where`-блоке их нужно именовать явно.
* `(X ⊗ Y).carrier` и `(𝟙_ _).carrier` дефиниционно равны
  `X.carrier ⊕ Y.carrier` и `PEmpty`, но `simp` не разворачивает цепочку
  проекций `структура → поле экземпляра`: в «носительных» целях нужен
  `rfl`, а для пустого носителя — `PEmpty.elim`, не `isEmptyElim`.
* `⊗` и `𝟙_` — **scoped** нотации: без
  `open CategoryTheory.MonoidalCategory` они не парсятся.
* `Fintype (α × β)` требует `Mathlib.Data.Fintype.Prod`; `Fintype.subtype` —
  `protected def`, а не экземпляр.
* `IsUnit.mul_eq_zero` в v4.18.0 **отсутствует**; сокращение обратимого
  множителя доказано вручную (`LinearPhase.eq_zero_of_unit_mul`).
* `linarith` в этом проекте не подключён; `norm_num` не закрывает
  `¬(-1 : ℝ) = 1` — используется `two_ne_zero`.
* Анонимные `instance` не имеют предсказуемого имени, поэтому для аудита
  они названы: `instCategory`, `instMonoidalCategory`,
  `instBraidedCategory`, `instSymmetricCategory`.
