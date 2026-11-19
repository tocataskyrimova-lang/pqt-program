# QCAT-TYPED-PHASE-008 — карта соответствия

Ответ на `QCAT_CLOSURE_007_ILORI_AUDIT_2026-11-07.md`, п.5.5:
`historical-source clause → Lean theorem → hypotheses → representation → verdict`,
с явным разделением **May** (`Ob = ℕ₀`) и **July** (`Ob = Σ*`).

## Обозначения вердиктов

| Метка | Значение |
|---|---|
| `MC` | machine-checked, без дополнительных гипотез |
| `MC-M` | machine-checked **внутри явно названной модели**; сама модель не отождествляется с источником |
| `MC-C` | machine-checked **условно** (гипотеза указана и она существенна) |
| `DEF` | только определено, проверки нет |
| `N/F` | не формализовано |

Сертификация: `lake build` — 898 целей, exit 0, 0 ошибок; 58 директив
`#print axioms`, 7 без аксиом, `sorryAx` — 0, пользовательских `axiom` — 0.
Множества аксиом: `{propext}`, `{propext, Quot.sound}`,
`{propext, Classical.choice, Quot.sound}`.
Лог: `provenance/build-logs/build-008-2026-11-07.log`.

---

## A. Источник «May» — `Q-Mathematics v3.md`, `Ob = ℕ₀`

`Ob(QCat) = N` (строка 11); «объект `n` = строка длины `n` из кодонов» (строка 15).

| § | Клауза (строки) | Lean | Гипотезы | Представление | Вердикт |
|---|---|---|---|---|---|
| A1 | `Ob = ℕ₀`, объект = длина цепочки (11, 15) | — | — | `BraidCore` имеет `Ob = Type`, а не `ℕ₀`. Длина появляется только как `Typed.objectMap_carrier : (objectMap w).carrier = Fin w.length` | `N/F` (осознанно: см. C) |
| A2 | `QCat = (Ob, Hom, ⊗, I, β)` (7) | `BraidCore.instCategory`, `instMonoidalCategory`, `instBraidedCategory` | `[CommMonoid K]` | `Type` / «фаза × биекция» / `Sum` / `PEmpty` / `Equiv.sumComm` | `MC-M` |
| A3 | `σᵢ(xᵢ,xᵢ₊₁) = ω(xᵢ,xᵢ₊₁)(xᵢ₊₁,xᵢ)` (70–84) | `BraidCore.braidingIso` (только перестановка) + `PhaseNaturality.sigma` (перестановка + фаза) | — | перестановка — структурная; `ω` — отдельно | `MC-M` |
| A4 | `ω : Σ×Σ → Q₋₁ˣ` (90) | `PhaseNaturality.sigma` при произвольном `K`; `BraidCore Kˣ` для единиц; `BraidCore.phase_isUnit`, `isIso_of_isUnit_phase` | `K` — коммутативный моноид; обратимость **не** требуется для YBE | скаляр | `MC-M` |
| A5 | **(B1)** local commutativity (116) | `QCatFormal.GeneralBraid.local_commutativity_general`; в `BraidCore` — через `BraidedCategory` | — | перестановки на `Fin n` | `MC` (для перестановочной части) |
| A6 | **(B2)** Yang–Baxter (136) | `QCatFormal.Historical.yang_baxter`; `BraidCore` — `hexagon_forward`, `hexagon_reverse` | — | — | `MC-M` |
| A7 | обратный braid `σᵢ⁻¹` (168–180) | `BraidedCategory.braiding : Iso`; `isIso_of_isUnit_phase` | — | — | `MC-M` |
| A8 | «перестановка **не обязана** быть симметричной» (110) | `BraidCore.instSymmetricCategory` — **обратное**: модель симметрична | — | — | `N/F`: несимметрический braiding **не** представлен |

**Ключевое следствие A8 (F1 аудита).** `braiding_double_eq_id` и экземпляр
`SymmetricCategory` — это машинное подтверждение того, что `BraidCore`
**не** является моделью несимметрического фазового braiding. Историческая
`ω` в `instBraidedCategory` не входит; она живёт отдельно и естественной
не является (`PhaseNaturality.generators_imply_constant`).

---

## B. Источник «July» — `PQT_QCAT_FINITE_PRESENTATION_INDEPENDENCE_MODELS_v0.1_RU.md`, `Ob = Σ*`

`Ob(QCat₀^fp) = Σ*` (строка 114); пустое слово — тензорная единица (117).

| § | Клауза (строки) | Lean | Гипотезы | Представление | Вердикт |
|---|---|---|---|---|---|
| B1 | `Ob = Σ*` (114) | `Typed.ColoredWord := List Glyph` | — | свободные цветные слова над `Fin 4` | `MC` (определение) |
| B2 | пустое слово `= 𝟙` (117) | `Typed.unitComparison : Fin 0 ≃ PEmpty` | — | **изоморфизм**, не равенство | `MC-M` (F2) |
| B3 | `r_{y←x} : x → y`, 12 штук (125–140) | `Typed.Rewrite` с `dom = [x]`, `cod = [y]`; `Generators.RewriteGen`, `card_rewriteGen = 12` | `x ≠ y` | типизированная стрелка | `MC` |
| B4 | отношение `r_{z←y}∘r_{y←x} = r_{z←x}` **не** постулируется (140–147) | `Typed.modelOf_comp_not_eq` | `x ≠ y`, `y ≠ z`, `x ≠ z` | глобальная модель не удовлетворяет отношению | `MC` (для модели) |
| B5 | `b_{x,y} : x⊗y → y⊗x`, 16 штук (141–152) | `Typed.Braid` с `dom = [x,y]`, `cod = [y,x]`; `Generators.BraidingGen`, `card_braidingGen = 16` | — | — | `MC` |
| B6 | продолжение на слова через hexagon/coherence (154–157) | `instBraidedCategory` (оба шестиугольника); `Generators.MultiPlacePhaseNatural` | — | — | `MC` для hexagon'ов; `DEF` для многоместной naturality |
| B7 | memory generators `δ² = δ` (§2.4) | — | — | — | `N/F` |
| B8 | dagger: `r_{y←x}† = r_{x←y}`, `b_{x,y}† = b_{x,y}⁻¹` (206–220) | — | — | — | `N/F` |

---

## C. Межуровневые мосты — и где они **не** отождествляют

| Мост | Lean | Тип связи | Вердикт |
|---|---|---|---|
| стрелка `r_{y←x}` → глобальная функция | `Typed.modelOf` | **интерпретация** (`def`), не отождествление | `MC-M` |
| модель уважает типизацию | `Typed.modelOf_respects_typing` | `[x].map (modelOf r) = [y]` | `MC` |
| модель верна (faithful) | `Typed.modelOf_injective` | разные стрелки → разные функции | `MC` |
| модель не добавляет соотношений | `Typed.modelOf_comp_not_eq` | композиция ≠ `r_{z←x}` | `MC` |
| слова → `BraidCore` | `Typed.objectMap`, `objectMap_carrier` | `w ↦ ⟨Fin w.length⟩`, carrier — `rfl` | `MC` |
| `[]` ↔ `𝟙_` | `Typed.unitComparison` | **изо**, не равенство | `MC-M` |
| `w ++ v` ↔ `w ⊗ v` | `Typed.appendComparison` | **изо** через `finSumFinEquiv.symm` | `MC-M` |
| `ColoredWord → BraidCore` как `MonoidalFunctor` | — | — | `N/F` |

**Почему `N/F` для функтора (F2).** `(w ++ v).length = w.length + v.length` —
это `List.length_append`, теорема, а не `rfl`; объектное равенство
`List.append` и `Sum` не дефиниционно. Сравнения — изоморфизмы, поэтому
речь может идти только о сильной моноидальной эквивалентности, а не о
строгом равенстве. Выдавать одно за другое было бы подменой; поэтому
функтор не объявлен, а разрыв зафиксирован в `appendComparison`.

**Почему `modelOf_injective` важен (F3).** Он показывает, что переход
«стрелка → глобальная замена» **ничего не теряет**: 12 генераторов
остаются 12 различными функциями. То есть модель не склеивает данные,
а лишь переинтерпретирует тип. Это ровно то, чего требовал аудит:
«не заменять их глобальными `Glyph → Glyph` без отдельного `model_of`» —
`model_of` теперь есть, и его свойства доказаны.

---

## D. §4: линейная картина и граница с делителями нуля

| Клауза | Lean | Гипотезы | Вердикт |
|---|---|---|---|
| `b_{x,z}` действует как `·ω(x,z)`, `r_{y←x}` как `·u_yx` | `LinearPhase.braidLin`, `rewriteLin`, `scal` | `[CommRing R]` | `MC` |
| натуральность слева: `u·(ω(y,z) − ω(x,z)) = 0` | `naturality_left_iff`, `naturality_left_iff_phases` | — | `MC` (точный критерий, ⇔) |
| натуральность справа: `u·(ω(z,y) − ω(z,x)) = 0` | `naturality_right_iff`, `naturality_right_iff_phases` | — | `MC` (⇔) |
| все `u_yx` обратимы ⇒ `ω` постоянна | `all_units_imply_constant` | `∀ x y, x ≠ y → IsUnit (u x y)` | `MC-C` |
| сокращение обратимоого множителя | `eq_zero_of_unit_mul` | `IsUnit a`, `a * b = 0` | `MC` |
| **безусловного no-go нет** | `zero_divisor_blocks_conclusion` | `R = ℝ × ℝ`, `u = e₊` | `MC` (свидетель) |
| тот же свидетель на линейных картах | `distinct_phases_same_morphism` | — | `MC` |

Свидетель: `u = e₊ = (1,0) ≠ 0`, `ω₁ = 1`, `ω₂ = ι = (1,−1)`; обе фазы
обратимы (`ι² = 1`), `ω₁ ≠ ω₂`, но `e₊·1 = e₊·ι`. Значит из `u ≠ 0`
**нельзя** вывести равенство фаз над кольцом с делителями нуля.
Утверждение аудита §4 подтверждено машинно.

**Чего свидетель НЕ делает:** он не проверяет согласованность с dagger и
memory. Это чистая фазово-переписывательная часть; полная контрмодель T0
не построена и не заявлена.

---

## E. Сводка вердиктов

| Отметка | Значение |
|---|---|
| `CONSTRUCTIVE_SYMMETRIC_BRAID_CORE` | `ACCEPT` — теперь ещё и `SymmetricCategory` в типе, а не в комментарии |
| `UNARY_GLOBAL_REPLACEMENT_CRITERION` | `ACCEPT_IN_SELECTED_MODEL` — модель названа и доказанно верна (`modelOf_injective`) |
| `LINEAR_PHASE_NATURALITY` | `ACCEPT` — обе натуральности в виде произведений, точные ⇔ |
| `NO_GO_WITHOUT_INVERTIBILITY` | `REFUTED` — контрпример `e₊` машинно проверен |
| `HISTORICAL_NON_SYMMETRIC_PHASED_QCAT` | `OPEN` — `BraidCore` симметрична, несимметрическая фазовая категория не построена |
| `FULL_T0 / MEMORY / DAGGER / QCAT_2L / PHYSICS` | `NOT_CLAIMED` |
