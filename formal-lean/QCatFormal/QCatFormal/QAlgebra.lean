-- Точечные импорты вместо агрегатора `Mathlib`: собирается ~1100 модулей
-- вместо 6332. Версии зафиксированы совместно: Lean 4.18.0 + Mathlib v4.18.0.
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Prod
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith.Frontend

-- Деление на ℝ невычислимо в Lean 4 (`Real.instDivInvMonoid`), поэтому
-- координаты `re`/`im` объявляются в невычислимой секции. Теоремы — Prop,
-- машинной проверке это не мешает.
noncomputable section

/-!
# Q₋₁ и идемпотенты e± (этап 1)

Канон `Q-Mathematics_v3.4_Canonical_PATCHED.md` §1:
`Qσ := ℝ ⊕ ιℝ`, `ι² = −σ`; при `σ = −1` получаем Q₋₁ (split-complex),
`δ² = δ`.

**Представление.** Вместо самописного `CommRing` используем стандартный
изоморфизм гиперболических чисел с покомпонентным кольцом `ℝ × ℝ`:

    a + b·ι  ↦  (a + b, a − b),      ι ↦ (1, −1).

Тогда `ι² = 1` — это буквально `CommRing (ℝ × ℝ)` из Mathlib, а
идемпотенты `e± = (1 ± ι)/2` превращаются в `(1,0)` и `(0,1)`.
Никаких новых аксиом, никаких `sorry`: весь этап 1 проверяется ядром Lean.
-/

namespace QCat.QAlgebra

/-- Q₋₁ как кольцо: `ℝ × ℝ` с покомпонентными операциями. -/
abbrev Qm1 := ℝ × ℝ

/-- Вложение `a + b·ι` в `(a+b, a−b)`. -/
def ofCoords (re im : ℝ) : Qm1 := (re + im, re - im)

/-- Обратные координаты. -/
def re (z : Qm1) : ℝ := (z.1 + z.2) / 2
def im (z : Qm1) : ℝ := (z.1 - z.2) / 2

/-- Гиперболическая единица ι. -/
def iota : Qm1 := (1, -1)

/-- Идемпотент e₊ = (1 + ι)/2. -/
def ePlus : Qm1 := (1, 0)

/-- Идемпотент e₋ = (1 − ι)/2. -/
def eMinus : Qm1 := (0, 1)

section Basic

theorem iota_sq : iota * iota = 1 := by
  ext <;> norm_num [iota]

theorem ofCoords_iota : ofCoords 0 1 = iota := by
  ext <;> norm_num [ofCoords, iota]

theorem re_ofCoords (a b : ℝ) : re (ofCoords a b) = a := by
  simp [re, ofCoords]

theorem im_ofCoords (a b : ℝ) : im (ofCoords a b) = b := by
  simp [im, ofCoords]

theorem ofCoords_re_im (z : Qm1) : ofCoords (re z) (im z) = z := by
  ext <;> simp [ofCoords, re, im] <;> ring

/-- `ι` не является ни нулём, ни единицей: Q₋₁ не поле. -/
theorem iota_ne_zero : iota ≠ 0 := by
  intro h
  have := congrArg Prod.fst h
  norm_num [iota] at this

theorem iota_ne_one : iota ≠ 1 := by
  intro h
  have := congrArg Prod.snd h
  norm_num [iota] at this

end Basic

section Idempotents

theorem ePlus_idem : ePlus * ePlus = ePlus := by
  ext <;> norm_num [ePlus]

theorem eMinus_idem : eMinus * eMinus = eMinus := by
  ext <;> norm_num [eMinus]

theorem ePlus_eMinus : ePlus * eMinus = 0 := by
  ext <;> norm_num [ePlus, eMinus]

theorem eMinus_ePlus : eMinus * ePlus = 0 := by
  ext <;> norm_num [ePlus, eMinus]

theorem ePlus_add_eMinus : ePlus + eMinus = 1 := by
  ext <;> norm_num [ePlus, eMinus]

theorem iota_decomp : iota = ePlus - eMinus := by
  ext <;> norm_num [iota, ePlus, eMinus]

/-- `e₊ = (1+ι)/2`. **Факт версии:** в Mathlib v4.18.0 у кольца `ℝ × ℝ`
    есть `OfNat` только для 0 и 1, но НЕТ `OfNat (ℝ × ℝ) 2` (нет `NatCast`
    для произведений). Поэтому скаляр 2 выписан явно парой `((2:ℝ),(2:ℝ))`. -/
theorem ePlus_formula : (1 + iota) / ((2 : ℝ), (2 : ℝ)) = ePlus := by
  ext <;> norm_num [iota, ePlus]

/-- `e₋ = (1−ι)/2`, скаляр 2 выписан явно по той же причине. -/
theorem eMinus_formula : (1 - iota) / ((2 : ℝ), (2 : ℝ)) = eMinus := by
  ext <;> norm_num [iota, eMinus]

/-- Q₋₁ имеет нетривиальные делители нуля — ещё одно отличие от поля. -/
theorem zero_divisors : ePlus ≠ 0 ∧ eMinus ≠ 0 ∧ ePlus * eMinus = 0 := by
  refine ⟨?_, ?_, ePlus_eMinus⟩
  · intro h; have := congrArg Prod.fst h; norm_num [ePlus] at this
  · intro h; have := congrArg Prod.snd h; norm_num [eMinus] at this

/-- В Q₋₁ НЕТ элемента с квадратом −1 (в отличие от ℂ):
    `z² = −1` означало бы `z.1² = −1` в ℝ.

    **ИСПРАВЛЕНО по QLP-04 (аудит Илори).** Из этого НЕ следует, будто
    монодромия `ω(x,y)·ω(y,x) = −1` недостижима над Q₋₁. Такая монодромия
    не требует `√−1`: достаточно ориентационно-зависимых обратимых фаз,
    например `ω(x,y)=1`, `ω(y,x)=−1` для `x<y`. `-1` — единица кольца Q₋₁.
    Явная Q₋₁-native контрмодель построена в `Qm1NBad.lean`.

    Что действительно коллидирует в исходниках: комплексная N-bad из
    `PQT_QCAT_INTRINSIC_BRAID_SPECTRUM_AUDIT` §7.1 задаёт `ω_xy = ω_yx = i`,
    а канон v3.4 объявляет фазы в `Q₋₁ˣ`. Дословно `i` не переносится, но
    тип препятствия (неравномерная монодромия) над Q₋₁ воспроизводим.
    Это коллизия формулировки, а не ошибка арифметики. -/
theorem no_sqrt_neg_one (z : Qm1) : z * z ≠ (-1 : Qm1) := by
  intro h
  have h1 : z.1 * z.1 = (-1 : ℝ) := by
    have := congrArg Prod.fst h
    simpa using this
  nlinarith [sq_nonneg z.1]

end Idempotents

section Classification

/-- Полная классификация идемпотентов Q₋₁: ровно 0, 1, e₊, e₋.

    Это и есть машинно проверяемая защита этапа 1: любое `δ` с `δ² = δ`
    обязано попадать в этот список.

    **ИСПРАВЛЕНО по QLP-04.** Утверждение «канон выбирает `δ = 1`» было
    неверным. Историческая спецификация противоречива: она одновременно
    задаёт `δ = ι` и `δ² = δ`, что невозможно (`ι² = 1 ≠ ι`). Реконструкция
    предлагает `δ_mem = e₊` как внешнюю конвенцию. Ни один из четырёх
    идемпотентов не выведен здесь как «правильный `δ`»: выбор `δ` остаётся
    вопросом сверки с QCat, а не арифметики. Доказательство классификации
    не изменено. -/
theorem idempotents_classified (z : Qm1) (hz : z * z = z) :
    z = 0 ∨ z = 1 ∨ z = ePlus ∨ z = eMinus := by
  have h1 : z.1 * z.1 = z.1 := by
    have := congrArg Prod.fst hz
    simpa using this
  have h2 : z.2 * z.2 = z.2 := by
    have := congrArg Prod.snd hz
    simpa using this
  have c1 : z.1 = 0 ∨ z.1 = 1 := by
    have hp : z.1 * (z.1 - 1) = 0 := by nlinarith
    rcases mul_eq_zero.mp hp with h | h
    · exact Or.inl (by nlinarith)
    · exact Or.inr (by nlinarith)
  have c2 : z.2 = 0 ∨ z.2 = 1 := by
    have hp : z.2 * (z.2 - 1) = 0 := by nlinarith
    rcases mul_eq_zero.mp hp with h | h
    · exact Or.inl (by nlinarith)
    · exact Or.inr (by nlinarith)
  rcases c1 with h1z | h1o <;> rcases c2 with h2z | h2o
  · left; ext <;> simp [h1z, h2z]
  · right; right; right; ext <;> simp [h1z, h2o, eMinus]
  · right; right; left; ext <;> simp [h1o, h2z, ePlus]
  · right; left; ext <;> simp [h1o, h2o]

/-- Обратно: все четыре элемента действительно идемпотентны. -/
theorem four_idempotents :
    (0 : Qm1) * 0 = 0 ∧ (1 : Qm1) * 1 = 1 ∧
      ePlus * ePlus = ePlus ∧ eMinus * eMinus = eMinus := by
  exact ⟨by ext <;> norm_num, by ext <;> norm_num, ePlus_idem, eMinus_idem⟩

end Classification

end QCat.QAlgebra

end
