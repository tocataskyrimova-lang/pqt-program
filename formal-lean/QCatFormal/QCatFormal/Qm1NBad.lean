import QCatFormal.QAlgebra
import Mathlib.Algebra.Ring.Prod
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.Linarith.Frontend

/-!
# Q₋₁-native контрмодель N-bad (QLP-04)

Аудит Илори указал на ошибочную интерпретацию `QAlgebra.no_sqrt_neg_one`:
отсутствие `√−1` в `Q₋₁ = ℝ × ℝ` **не** запрещает монодромию
`ω(x,y)·ω(y,x) = −1`. Комплексная N-bad (`ω_xy = ω_yx = i`) действительно
не переносится дословно, но то же препятствие воспроизводится уже единицами
кольца Q₋₁, если фазы ориентационно-зависимы:

    ω(x,y) = 1   при x < y,
    ω(y,x) = −1  при x < y,
    самопары и пары с δ (глиф 3) дают 1.

`−1` — обратимый элемент `Q₋₁` (`(−1)·(−1)=1`), никакого `i` не требуется.

**Что доказано здесь.**
* Каждая фаза `ω(x,y)` обратима с явным свидетелем (`1` или `−1`).
* YBE для фазовой таблицы (коммутативность Q₋₁).
* Существование пары с монодромией `−1`, т.е. несимметричный braiding
  без смены меток.
* Таблица не является скалярным flip'ом.
* При нулевом образе rewrite-генератора naturality пуста; при ненулевом
  та же пара фаз её нарушает (`F = −F ⇒ F = 0` в характеристике 0).

**Границы (`not_claimed`).** Это по-прежнему *скалярная фазовая модель* на
4 глифах, а не модель всей конечной презентации `T₀` (12 генераторов,
relations, функтор `F`, матрица `R` на `V⊗V`) и не теорема N1.
Физические/PTR утверждения не изменяются.
-/

namespace QCat.Qm1NBad

open QCat.QAlgebra (Qm1)

/-- Четыре глифа `Σ = {α, β, γ, δ}`; `3` — δ (Tamas/memory). -/
abbrev Glyph := Fin 4

/-- Фазовая таблица со значениями в единицах `Q₋₁ˣ` (`1` и `−1`).
    Сравнения выписаны через `Fin.val`, чтобы конечные случаи сводились
    `norm_num` без привлечения `DecidableEq ℝ`. -/
def omegaQ (x y : Glyph) : Qm1 :=
  if x.val = y.val ∨ x.val = 3 ∨ y.val = 3 ∨ x.val < y.val then 1 else -1

/-- Таблица принимает только два значения — обе единицы кольца. -/
theorem omegaQ_values (x y : Glyph) : omegaQ x y = 1 ∨ omegaQ x y = -1 := by
  by_cases h : x.val = y.val ∨ x.val = 3 ∨ y.val = 3 ∨ x.val < y.val
  · left; rw [omegaQ, if_pos h]
  · right; rw [omegaQ, if_neg h]

/-- **Обратимость фаз над Q₋₁**: явный двусторонний обратный. -/
theorem omegaQ_invertible (x y : Glyph) :
    ∃ u : Qm1, omegaQ x y * u = 1 ∧ u * omegaQ x y = 1 := by
  rcases omegaQ_values x y with h | h
  · refine ⟨1, ?_, ?_⟩ <;> rw [h] <;> ext <;> norm_num
  · refine ⟨-1, ?_, ?_⟩ <;> rw [h] <;> ext <;> norm_num

/-- YBE выполняется для любой таблицы фаз: Q₋₁ коммутативно. -/
theorem omegaQ_YBE (x y z : Glyph) :
    omegaQ x y * omegaQ x z * omegaQ y z =
      omegaQ y z * omegaQ x z * omegaQ x y := by
  simp [mul_assoc, mul_comm, mul_left_comm]

/-- Неравномерная монодромия на активных различных парах. -/
theorem omegaQ_monodromy (x y : Glyph)
    (hx : x ≠ 3) (hy : y ≠ 3) (hxy : x ≠ y) :
    omegaQ x y * omegaQ y x = -1 := by
  fin_cases x <;> fin_cases y <;> simp_all [omegaQ]

/-- Конкретная пара `(0,1)` даёт монодромию `−1`. -/
theorem omegaQ_monodromy_01 : omegaQ 0 1 * omegaQ 1 0 = -1 := by
  ext <;> norm_num [omegaQ]

/-- Таблица не является скалярным flip'ом: `ω(0,0)=1`, но `ω(1,0)=−1`. -/
theorem omegaQ_not_scalar_flip :
    ¬ ∃ r : Qm1, ∀ x y : Glyph, omegaQ x y = r := by
  rintro ⟨r, hr⟩
  have h00 : omegaQ 0 0 = r := hr 0 0
  have h10 : omegaQ 1 0 = r := hr 1 0
  have hEq : (1 : Qm1) = -1 := by
    calc
      (1 : Qm1) = omegaQ 0 0 := by norm_num [omegaQ]
      _ = r := h00
      _ = omegaQ 1 0 := h10.symm
      _ = -1 := by norm_num [omegaQ]
  have := congrArg Prod.fst hEq
  norm_num at this

/-- При нулевом образе rewrite-генератора naturality не ограничивает braiding. -/
theorem zero_image_naturality_trivial_Qm1 (R : Qm1) :
    ∃ F : Qm1, F = 0 ∧ R * F = F * R :=
  ⟨0, rfl, by simp⟩

/-- При ненулевом образе пары фаз `1` и `−1` естественность нарушается.
    `F = −F` влечёт `F = 0` в ℝ×ℝ (характеристика 0). -/
theorem nonzero_image_breaks_Qm1NBad (F : Qm1) (hF : F ≠ 0)
    (hNat : (1 : Qm1) * F = F * (-1 : Qm1)) : False := by
  have h1 := congrArg Prod.fst hNat
  have h2 := congrArg Prod.snd hNat
  simp at h1 h2
  have hF1 : F.1 = 0 := by linarith
  have hF2 : F.2 = 0 := by linarith
  apply hF
  ext <;> assumption

/-- **Сводная Q₋₁-native контрмодель.** Все фазы — единицы Q₋₁, YBE верно,
    монодромия `−1` достижима, таблица не скалярна, нулевой образ тривиален.
    `not_claimed(N1)`, `not_claimed(T0)`, `not_claimed(BraidedCategory QCat)`. -/
theorem Qm1_native_counterexample :
    ∃ omega : Glyph → Glyph → Qm1,
      (∀ x y : Glyph, ∃ u : Qm1, omega x y * u = 1 ∧ u * omega x y = 1) ∧
      (∀ x y z : Glyph,
        omega x y * omega x z * omega y z =
          omega y z * omega x z * omega x y) ∧
      (∃ x y : Glyph, omega x y * omega y x = -1) ∧
      (∀ R : Qm1, ∃ F : Qm1, F = 0 ∧ R * F = F * R) ∧
      (¬ ∃ r : Qm1, ∀ x y : Glyph, omega x y = r) := by
  refine ⟨omegaQ, omegaQ_invertible, ?_, ?_, ?_, omegaQ_not_scalar_flip⟩
  · intro x y z
    exact omegaQ_YBE x y z
  · exact ⟨0, 1, omegaQ_monodromy_01⟩
  · intro R
    exact zero_image_naturality_trivial_Qm1 R

end QCat.Qm1NBad
