/-
  QCAT-CAT-BRIDGE-001 · M1 — FINITE STOCHASTIC REALIZATION
  ========================================================

  Соглашения (фиксируются здесь и не меняются ниже):
  * Состояния — конечный тип `α`; распределение — **строка** (row-vector):
    `(p ⬝ Q) j = ∑ i, p i * Q i j`.
  * Композиция — матричное произведение `M * N`, т.е. «сначала M, потом N».
  * Всё считается в точной арифметике над `ℚ`. Никаких приближений.

  ЧТО ЗДЕСЬ НЕ УТВЕРЖДАЕТСЯ:
  * что веса `w(x,y)` ОПРЕДЕЛЯЮТСЯ переписываниями QCat или фазами `Q₋₁`;
  * что произвольный символический морфизм отображается в стохастическое ядро
    функториально. Наоборот, ниже доказана обструкция
    (`stochastic_phase_forces_one`): стохастичность уничтожает фазу.
-/
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Fintype.Sum
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Data.Fin.VecNotation
import Mathlib.Algebra.Order.Ring.Rat
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp

open scoped BigOperators

namespace QCat
namespace Bridge

/-! ## 0. Глифы

В QCat-008 `Glyph = Fin 4`. Здесь это зафиксировано явно, вместе с тривиальным
(но именованным) мостом `Glyph ≃ Fin 4`, чтобы соответствие было проверяемым,
а не подразумеваемым. -/

abbrev Glyph := Fin 4

/-- Мост `Glyph ≃ Fin 4`. В QCat-008 глифы — ровно `Fin 4`, поэтому
    эквивалентность тождественная; она всё равно выписана явно. -/
def glyphEquiv : Glyph ≃ Fin 4 := Equiv.refl _

@[simp] theorem glyphEquiv_apply (g : Glyph) : glyphEquiv g = g := rfl

theorem glyphEquiv_symm_apply (g : Fin 4) : glyphEquiv.symm g = g := rfl

/-- Внедиагональных типизированных пар ровно 12 — это те же 12 генераторов
    `r_{y←x}` (`x ≠ y`) из первичного текста T0. -/
theorem card_offdiag_glyph :
    (Finset.univ.filter (fun p : Glyph × Glyph => p.1 ≠ p.2)).card = 12 := by
  decide

/-! ## 1. Стохастические матрицы над `ℚ` -/

/-- Конечная стохастическая матрица: неотрицательные элементы, сумма каждой
    строки равна 1. Соглашение — row-vector. -/
structure StochMatrix (α : Type*) [Fintype α] [DecidableEq α] where
  toMatrix : Matrix α α ℚ
  nonneg : ∀ i j, 0 ≤ toMatrix i j
  row_sum : ∀ i, ∑ j, toMatrix i j = 1

namespace StochMatrix

variable {α : Type*} [Fintype α] [DecidableEq α]

instance : CoeFun (StochMatrix α) (fun _ => α → α → ℚ) := ⟨fun Q => Q.toMatrix⟩

@[simp] theorem coe_apply (Q : StochMatrix α) (i j : α) : Q i j = Q.toMatrix i j := rfl

/-- Замыкание по умножению: композиция двух стохастических матриц снова
    стохастическая. Доказаны и неотрицательность, и единичная сумма строк. -/
def mul (M N : StochMatrix α) : StochMatrix α where
  toMatrix := M.toMatrix * N.toMatrix
  nonneg i j := by
    simp only [Matrix.mul_apply]
    exact Finset.sum_nonneg fun k _ => mul_nonneg (M.nonneg i k) (N.nonneg k j)
  row_sum i := by
    simp only [Matrix.mul_apply]
    rw [Finset.sum_comm]
    have h1 : ∀ k, ∑ j, M.toMatrix i k * N.toMatrix k j
        = M.toMatrix i k * ∑ j, N.toMatrix k j := by
      intro k
      rw [Finset.mul_sum]
    simp only [h1, N.row_sum, mul_one]
    exact M.row_sum i

/-- Единичная стохастическая матрица. -/
def one : StochMatrix α where
  toMatrix := 1
  nonneg i j := by
    rw [Matrix.one_apply]
    split <;> norm_num
  row_sum i := by
    simp [Matrix.one_apply]

instance : One (StochMatrix α) := ⟨one⟩
instance : Mul (StochMatrix α) := ⟨mul⟩

@[simp] theorem mul_apply (M N : StochMatrix α) (i j : α) :
    (M * N) i j = ∑ k, M i k * N k j := rfl

@[simp] theorem one_apply (i j : α) :
    (1 : StochMatrix α) i j = if i = j then 1 else 0 := rfl

/-- Экстенсиональность по носителю матрицы. -/
@[ext] theorem ext {M N : StochMatrix α} (h : M.toMatrix = N.toMatrix) : M = N := by
  cases M; cases N; simp_all

/-- Итерация: `Q^n` — переход за `n` шагов. -/
def pow (M : StochMatrix α) : ℕ → StochMatrix α
  | 0 => 1
  | n + 1 => pow M n * M

@[simp] theorem pow_zero (M : StochMatrix α) : M.pow 0 = 1 := rfl
@[simp] theorem pow_succ (M : StochMatrix α) (n : ℕ) : M.pow (n + 1) = M.pow n * M := rfl

/-- Композиция ассоциативна (на уровне матриц). -/
theorem mul_assoc_toMatrix (M N P : StochMatrix α) :
    (M * N) * P = M * (N * P) := by
  apply StochMatrix.ext
  show (M.toMatrix * N.toMatrix) * P.toMatrix = M.toMatrix * (N.toMatrix * P.toMatrix)
  exact Matrix.mul_assoc _ _ _

/-! ## 2. Ядро из весов `w(x,y)` и удержания `d(x)`

Веса — **выбранные дополнительные данные**, а не функция от переписываний QCat.
Это прямо зафиксировано в контракте (п.1) и повторено в `CORRESPONDENCE.md`. -/

/-- Стохастическое ядро `Q_w`: вне диагонали — `w x y`, на диагонали — `d x`.
    Требование `∑_{y≠x} w x y + d x = 1` делает его стохастическим. -/
def ofWeights (w : Glyph → Glyph → ℚ) (d : Glyph → ℚ)
    (hw : ∀ x y, x ≠ y → 0 ≤ w x y) (hd : ∀ x, 0 ≤ d x)
    (hsum : ∀ x, (∑ y in Finset.univ.erase x, w x y) + d x = 1) : StochMatrix Glyph where
  toMatrix x y := if x = y then d x else w x y
  nonneg x y := by
    dsimp only
    by_cases h : x = y
    · subst h; simpa using hd x
    · rw [if_neg h]; exact hw x y h
  row_sum x := by
    dsimp only
    rw [← Finset.add_sum_erase (Finset.univ : Finset Glyph)
      (fun j => if x = j then d x else w x j) (Finset.mem_univ x)]
    rw [if_pos rfl]
    have hcongr : ∑ j ∈ Finset.univ.erase x, (if x = j then d x else w x j)
        = ∑ j ∈ Finset.univ.erase x, w x j := by
      refine Finset.sum_congr rfl ?_
      intro j hj
      rw [if_neg (Finset.ne_of_mem_erase hj).symm]
    rw [hcongr, add_comm]
    exact hsum x

/-! ## 3. Точные фикстуры

### 3.1 `Q4` — равномерная на четырёх состояниях -/

/-- Равномерное ядро: все элементы `1/4`. -/
def Q4 : StochMatrix Glyph where
  toMatrix := fun _ _ => 1 / 4
  nonneg i j := by norm_num
  row_sum i := by
    simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
    norm_num

theorem Q4_apply (i j : Glyph) : Q4 i j = 1 / 4 := rfl

/-- Явная проверка: `Q4` действительно стохастическая (не только по типу). -/
theorem Q4_row_sums (i : Glyph) : ∑ j, Q4 i j = 1 := Q4.row_sum i

/-! ### 3.2 `QNU` — неравномерная и несимметричная фикстура

Нужна, чтобы результат не был артефактом равномерности. Матрица намеренно
несимметрична: `QNU 0 1 = 1/3`, но `QNU 1 0 = 0`. -/

/-- Неравномерное несимметричное ядро на `Fin 4`. -/
def QNUmat : Matrix Glyph Glyph ℚ :=
  ![![1 / 2, 1 / 3, 1 / 6, 0],
    ![0, 1 / 2, 1 / 4, 1 / 4],
    ![1 / 4, 0, 1 / 2, 1 / 4],
    ![1 / 8, 1 / 8, 1 / 8, 5 / 8]]

def QNU : StochMatrix Glyph where
  toMatrix := QNUmat
  nonneg i j := by
    fin_cases i <;> fin_cases j <;> simp [QNUmat] <;> norm_num
  row_sum i := by
    fin_cases i <;> simp [QNUmat, Fin.sum_univ_four] <;> norm_num

theorem QNU_row_sums (i : Glyph) : ∑ j, QNU i j = 1 := QNU.row_sum i

/-- Фикстура действительно несимметрична (иначе тест на «не переобучились
    под равномерный/симметричный случай» ничего не проверяет). -/
theorem QNU_not_symmetric : QNU 0 1 ≠ QNU 1 0 := by
  have h1 : QNU 0 1 = 1 / 3 := rfl
  have h2 : QNU 1 0 = 0 := rfl
  rw [h1, h2]
  norm_num

/-! ## 4. ОБСТРУКЦИЯ: стохастичность уничтожает фазу

Контракт требует не предполагать, что символический морфизм отображается в
стохастическое ядро функториально, а вывести закон или сообщить обструкцию.
Ниже — точная обструкция.

Историческая фаза `ω` реализует сплетение как `ω(a,b) · swap`. Если требовать,
чтобы результат был **стохастической** матрицей, то сумма строк `ω · swap`
равна `ω`, а должна быть `1`. Значит `ω = 1` для любого состояния.

То есть **прямая** («вес × перестановка») стохастическая реализация фазового
сплетения вынужденно теряет фазу: остаётся чистый своп. Это не «неудобство
формализации», а содержательное утверждение о границе между QCat и
стохастикой — но именно в этой области. Скрытые состояния, нелинейные
отображения и неверные наблюдательные отображения теоремой не покрываются;
пример неверной, но мультипликативной реализации — `SignRealization.lean`. -/

/-- Матрица чистого свопа на парах состояний: `(a,b) ↦ (b,a)`. -/
def swapMatrix (β : Type*) [Fintype β] [DecidableEq β] : Matrix (β × β) (β × β) ℚ :=
  fun p q => if q = (p.2, p.1) then 1 else 0

theorem swapMatrix_row_sum (β : Type*) [Fintype β] [DecidableEq β] (p : β × β) :
    ∑ q, swapMatrix β p q = 1 := by
  simp [swapMatrix]

/-- Сумма строк матрицы `ω · swap` равна `ω`. -/
theorem scaled_swap_row_sum (β : Type*) [Fintype β] [DecidableEq β] (ω : ℚ) (p : β × β) :
    ∑ q, ω * swapMatrix β p q = ω := by
  simp [swapMatrix]

/-- **Обструкция (в узкой области).** Если `ω · swap` — стохастическая матрица
    (сумма каждой строки равна 1), то `ω = 1`.

    ОБЛАСТЬ ПРИМЕНЕНИЯ (уточнено по ревизии координатора, ADDENDUM-002 / H3).
    Это утверждение о **прямой** реализации фазового сплетения в виде
    «скалярный вес × перестановка»: в каждой строке ровно один ненулевой
    вход, равный `ω`. Оно **не** исключает:
      * реализации со скрытыми состояниями (расширение носителя);
      * нелинейные отображения «морфизм → ядро»;
      * неверные (nonfaithful) наблюдательные отображения — конкретный пример
        такой реализации знаковой группы см. `QCat.Bridge.Mmat`
        (`SignRealization.lean`, `Mmat_not_injective`).
    Универсального запрета «нетривиальная фаза нереализуема вообще» здесь
    не утверждается и не должно выводиться из этой теоремы. -/
theorem stochastic_phase_forces_one (β : Type*) [Fintype β] [DecidableEq β] [Nonempty β]
    (ω : ℚ) (h : ∀ p : β × β, ∑ q, ω * swapMatrix β p q = 1) : ω = 1 := by
  have := h (Classical.arbitrary (β × β))
  rwa [scaled_swap_row_sum] at this

/-- Следствие в узкой форме: при `ω ≠ 1` матрица `ω · swap` **не**
    стохастическая. Область — та же, что у `stochastic_phase_forces_one`. -/
theorem nontrivial_phase_not_stochastic (β : Type*) [Fintype β] [DecidableEq β] [Nonempty β]
    (ω : ℚ) (hω : ω ≠ 1) : ¬ ∀ p : β × β, ∑ q, ω * swapMatrix β p q = 1 := by
  intro h
  exact hω (stochastic_phase_forces_one β ω h)

end StochMatrix

end Bridge
end QCat
