import Mathlib.Data.Complex.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

/-!
# Естественность и классификация переписываний (этап 3)

Источник: `PQT_QCAT_INTRINSIC_BRAID_SPECTRUM_AUDIT_v0.1_RU.md`
(теорема N1, §7 «Почему bare T₀ всё ещё недостаточно», контрмодель N-bad)
и `PQT_QCAT_FINITE_PRESENTATION_INDEPENDENCE_MODELS_v0.1_RU.md` §2.2, §2.6.

Суть находки Аргона: bare теория `T₀` задаёт 12 rewrite-generator'ов, но НЕ
содержит отношения `F(r_{y←x}) ≠ 0`. Если функтор посылает их в нуль,
условие естественности `R(A⊗B) = (B⊗A)R` вырождается в `0 = 0` и перестаёт
ограничивать braiding. Поэтому `T₀ ⊬ DCHAR4`, а «полная классификация»
верна только с явно объявленной гипотезой ненулевого образа.

**Что здесь доказано.** *Абстрактная скалярная* модель на 4 глифах над **ℂ**:
YBE, контрмодель N-bad (нескалярный flip, монодромия −1), тривиальность
naturality при нулевом образе и её нетривиальность при ненулевом.

**Граница применимости (QLP-04).** Комплексная таблица `ω_xy = ω_yx = i` —
модель над ℂ, а не над `Q₋₁ˣ`: в Q₋₁ нет `√−1` (`QAlgebra.no_sqrt_neg_one`).
Однако **неравномерная монодромия `−1` над Q₋₁ достижима** без `√−1` —
ориентационно-зависимыми единицами `1` и `−1`. Отдельная Q₋₁-native
контрмодель построена в `Qm1NBad.lean`; этот файл её не заменяет и не
утверждает, что комплексная N-bad дословно переносится в Q₋₁.

**ИСПРАВЛЕНО по QLP-05.** Теорема, ранее называвшаяся
`T0_admits_nonscalar_braiding`, переименована в
`scalar_zero_image_counterexample`: она доказывает существование скалярной
таблицы фаз с `R·0 = 0·R`, а **не** контрмодель всей конечной презентации `T₀`.

**Что здесь НЕ заявлено (`not_claimed`).**
* `not_claimed(N1)`: теорема N1 в полной формулировке (`M₄(ℂ)`, коммутант
  `M₁₆`, `R = rP`) не формализована — нужна матричная инфраструктура.
* `not_claimed(T0)`: 12 rewrite-генераторов `r_{y←x}`, их relations,
  функтор `F` и общая матрица `R` на `V⊗V` здесь не заданы.
* `not_claimed(BraidedCategory QCat)`, `not_claimed(QCat₂L)`, физические/PTR
  предсказания не выводятся.

Этот файл фиксирует только *логическую* часть ошибки — обязательность
гипотезы `F(r) ≠ 0` — а не заменяет собой N1 или модель `T₀`.
-/

namespace QCat.Naturality

/-- Четыре глифа `Σ = {α, β, γ, δ}`. `3` — δ (Tamas/memory). -/
abbrev Glyph := Fin 4

def isActive (x : Glyph) : Prop := x ≠ 3

/-- Контрмодель N-bad (§7.1): `ω_xx = 1`, пары с δ дают 1, активные
    различные пары дают `i`, т.е. `ω_xy ω_yx = −1`. -/
def omegaNBad (x y : Glyph) : ℂ :=
  if x = y then 1
  else if x = 3 ∨ y = 3 then 1
  else Complex.I

/-- Для скалярных фаз YBE выполняется тождественно (коммутативность ℂ). -/
theorem phase_YBE (omega : Glyph → Glyph → ℂ) (x y z : Glyph) :
    omega x y * omega x z * omega y z = omega y z * omega x z * omega x y := by
  ring

theorem omegaNBad_self (x : Glyph) : omegaNBad x x = 1 := by
  simp [omegaNBad]

theorem omegaNBad_active (x y : Glyph) (hx : x ≠ 3) (hy : y ≠ 3) (hxy : x ≠ y) :
    omegaNBad x y = Complex.I := by
  simp [omegaNBad, hx, hy, hxy]

/-- Неравномерная монодромия на активных парах ⇒ braiding не симметричный. -/
theorem omegaNBad_monodromy (x y : Glyph) (hx : x ≠ 3) (hy : y ≠ 3) (hxy : x ≠ y) :
    omegaNBad x y * omegaNBad y x = -1 := by
  rw [omegaNBad_active x y hx hy hxy, omegaNBad_active y x hy hx hxy.symm]
  exact Complex.I_mul_I

/-- «Скалярный flip»: `R = r·P`, т.е. фаза не зависит от цветов. -/
def IsScalarFlip (omega : Glyph → Glyph → ℂ) : Prop :=
  ∃ r : ℂ, ∀ x y : Glyph, omega x y = r

/-- `I ≠ 1` как вспомогательная лемма. -/
theorem I_ne_one : Complex.I ≠ (1 : ℂ) := by
  intro h
  have him := congrArg Complex.im h
  norm_num at him

theorem omegaNBad_not_scalar_flip : ¬ IsScalarFlip omegaNBad := by
  rintro ⟨r, hr⟩
  have h00 : (1 : ℂ) = r := by simpa [omegaNBad] using hr 0 0
  have h01 : Complex.I = r := by simpa [omegaNBad] using hr 0 1
  exact I_ne_one (h01.trans h00.symm)

/-- При нулевом образе rewrite-генератора naturality пуста: она не накладывает
    ни одного ограничения на R (`R·0 = 0·R` при любом R). -/
theorem zero_image_naturality_trivial (R : ℂ) :
    ∃ F : ℂ, F = 0 ∧ R * F = F * R :=
  ⟨0, rfl, by ring⟩

/-- При ненулевом образе та же фазовая модель N-bad естественность нарушает:
    `i·F = F·1` при `F ≠ 0` влечёт `i = 1`. -/
theorem nonzero_image_breaks_NBad (F : ℂ) (hF : F ≠ 0)
    (hNat : Complex.I * F = F * 1) : False := by
  have hEq : Complex.I * F = 1 * F := by simpa [mul_comm] using hNat
  have hI : Complex.I = (1 : ℂ) := (mul_right_cancel₀ hF) hEq
  exact I_ne_one hI

/-- **QLP-05.** Скалярная контрольная модель: при нулевом образе rewrite-генератора
    YBE и naturality не запрещают нескалярную фазовую таблицу.

    Это НЕ контрмодель конечной презентации `T₀`: здесь нет 12 генераторов,
    relations, функтора `F` и матрицы `R` на `V⊗V`. Название исправлено по
    требованию аудита (было `T0_admits_nonscalar_braiding`).
    `not_claimed(N1)`, `not_claimed(T0)`. -/
theorem scalar_zero_image_counterexample :
    ∃ omega : Glyph → Glyph → ℂ,
      (∀ x y z : Glyph,
        omega x y * omega x z * omega y z = omega y z * omega x z * omega x y) ∧
      (∀ R : ℂ, ∃ F : ℂ, F = 0 ∧ R * F = F * R) ∧
      ¬ IsScalarFlip omega := by
  refine ⟨omegaNBad, ?_, ?_, omegaNBad_not_scalar_flip⟩
  · intro x y z; exact phase_YBE omegaNBad x y z
  · intro R; exact zero_image_naturality_trivial R

/-- Защита от возвращения ошибки: условие `F(r) ≠ 0` обязано входить в
    формулировку rigidity. Без него класс допустимых braiding'ов шире `r·P`. -/
theorem nondegeneracy_is_essential :
    (∃ omega : Glyph → Glyph → ℂ, ¬ IsScalarFlip omega) := by
  exact ⟨omegaNBad, omegaNBad_not_scalar_flip⟩

end QCat.Naturality
