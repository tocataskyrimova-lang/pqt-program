/-
  QCAT-CAT-BRIDGE-001 · M2 — OBSERVER TRACE / FIRST RETURN
  ========================================================

  Разбиение `S ≃ V ⊕ H`: `V` — наблюдаемые состояния, `H` — скрытые.
  Блочная запись `Q = [[A, B], [C, D]]`.

  След наблюдателя:  `Tr_V(Q) = A + B (I − D)⁻¹ C`.

  ГЛАВНОЕ ОГРАНИЧЕНИЕ (п.2 контракта): формула **не** вводится как равенство
  для произвольной `D`. Требуется *сертифицированный* обратный: явная матрица
  `Dinv` вместе с доказательством `Dinv * (I − D) = 1`. Без него `Tr_V`
  не определён, и ниже доказано, почему: при поглощающем скрытом классе
  (`D = I`) обратного нет вовсе (`absorbing_no_inverse`), а «наивный» след
  вырождается в субстохастическую матрицу, которую нельзя молча
  нормировать (`absorbing_gives_substochastic`).

  ЧТО ДОКАЗАНО:
  * `traceV_nonneg` — вероятности первого возвращения неотрицательны;
  * `traceV_row_sum` — суммы строк равны 1 при условии возврата;
  * `geom_partial` — связь с рядом Неймана в форме точного тождества
    с остатком (не как формальное равенство для произвольной `D`);
  * точные фикстуры `Q_RGB` и `Q4`.
-/
import QCatCatBridge.MarkovKernel

open scoped BigOperators

namespace QCat
namespace Bridge

open StochMatrix

variable {V H : Type*} [Fintype V] [DecidableEq V] [Fintype H] [DecidableEq H]

/-! ## 1. Блоки -/

/-- Блок `V → V`. -/
def blockA (Q : StochMatrix (V ⊕ H)) : Matrix V V ℚ :=
  fun i j => Q.toMatrix (Sum.inl i) (Sum.inl j)

/-- Блок `V → H` (наблюдаемое → скрытое). -/
def blockB (Q : StochMatrix (V ⊕ H)) : Matrix V H ℚ :=
  fun i k => Q.toMatrix (Sum.inl i) (Sum.inr k)

/-- Блок `H → V` (скрытое → наблюдаемое). -/
def blockC (Q : StochMatrix (V ⊕ H)) : Matrix H V ℚ :=
  fun k j => Q.toMatrix (Sum.inr k) (Sum.inl j)

/-- Блок `H → H` (скрытое → скрытое). -/
def blockD (Q : StochMatrix (V ⊕ H)) : Matrix H H ℚ :=
  fun k l => Q.toMatrix (Sum.inr k) (Sum.inr l)

/-- `I − D` в явном виде (без `1 -` на матрицах, чтобы суммы раскрывались
    предсказуемо). -/
def oneMinusD (Q : StochMatrix (V ⊕ H)) : Matrix H H ℚ :=
  fun k l => (if k = l then (1 : ℚ) else 0) - blockD Q k l

/-! ## 2. Разложение сумм строк по блокам -/

theorem row_split_V (Q : StochMatrix (V ⊕ H)) (i : V) :
    (∑ j, blockA Q i j) + (∑ k, blockB Q i k) = 1 := by
  have h := Q.row_sum (Sum.inl i)
  rw [Fintype.sum_sum_type] at h
  simpa [blockA, blockB] using h

theorem row_split_H (Q : StochMatrix (V ⊕ H)) (k : H) :
    (∑ j, blockC Q k j) + (∑ l, blockD Q k l) = 1 := by
  have h := Q.row_sum (Sum.inr k)
  rw [Fintype.sum_sum_type] at h
  simpa [blockC, blockD] using h

/-- Сумма строк блока `C` равна сумме строк `I − D`: это ровно «вероятность
    уйти из скрытого состояния в наблюдаемое = 1 − вероятность остаться». -/
theorem rowsum_C_eq (Q : StochMatrix (V ⊕ H)) (k : H) :
    ∑ j, blockC Q k j = ∑ m, oneMinusD Q k m := by
  have h := row_split_H Q k
  have h1 : ∑ m, oneMinusD Q k m
      = (∑ m, (if k = m then (1 : ℚ) else 0)) - ∑ m, blockD Q k m := by
    simp only [oneMinusD]
    exact Finset.sum_sub_distrib
  have hone : ∑ m, (if k = m then (1 : ℚ) else 0) = 1 := by simp
  rw [h1, hone]
  linarith

/-! ## 3. След -/

/-- `Tr_V(Q) = A + B · Dinv · C`. Определение **требует** явного `Dinv`;
    никакого «взятия обратного по умолчанию» здесь нет. -/
def traceV (Q : StochMatrix (V ⊕ H)) (Dinv : Matrix H H ℚ) : Matrix V V ℚ :=
  blockA Q + blockB Q * Dinv * blockC Q

/-- Вероятности первого возвращения неотрицательны. -/
theorem traceV_nonneg (Q : StochMatrix (V ⊕ H)) (Dinv : Matrix H H ℚ)
    (hD : ∀ k l, 0 ≤ Dinv k l) (i j : V) : 0 ≤ traceV Q Dinv i j := by
  have hBC : 0 ≤ (blockB Q * Dinv * blockC Q) i j := by
    simp only [Matrix.mul_apply]
    refine Finset.sum_nonneg fun k _ => ?_
    refine mul_nonneg ?_ (Q.nonneg _ _)
    exact Finset.sum_nonneg fun l _ => mul_nonneg (Q.nonneg _ _) (hD l k)
  exact add_nonneg (Q.nonneg _ _) hBC

/-- Вспомогательное: `∑ k, Dinv l k * (∑ j, C k j) = 1` при `Dinv * (I−D) = 1`.
    Это и есть содержание условия возврата. -/
theorem inner_row_sum (Q : StochMatrix (V ⊕ H)) (Dinv : Matrix H H ℚ)
    (hDinv : Dinv * oneMinusD Q = 1) (l : H) :
    ∑ k, Dinv l k * (∑ j, blockC Q k j) = 1 := by
  have hC : ∀ k : H, (∑ j, blockC Q k j) = ∑ m, oneMinusD Q k m :=
    fun k => rowsum_C_eq Q k
  simp only [hC, Finset.mul_sum]
  rw [Finset.sum_comm]
  have hstep : ∀ m : H, ∑ k, Dinv l k * oneMinusD Q k m
      = (Dinv * oneMinusD Q) l m := by
    intro m
    simp [Matrix.mul_apply]
  simp only [hstep, hDinv]
  simp [Matrix.one_apply]

/-- **Суммы строк следа равны 1.** Условие — сертифицированный левый обратный
    `Dinv * (I − D) = 1`; оно же влечёт формулировку контракта
    `(I − D)⁻¹ C 1_V = 1_H` (см. `inner_row_sum`).

    Смысл: если из каждого скрытого состояния, достижимого из `V`, возврат
    в `V` происходит почти наверное, то след снова стохастичен. -/
theorem traceV_row_sum (Q : StochMatrix (V ⊕ H)) (Dinv : Matrix H H ℚ)
    (hDinv : Dinv * oneMinusD Q = 1) (i : V) :
    ∑ j, traceV Q Dinv i j = 1 := by
  have hBC : ∑ j, (blockB Q * Dinv * blockC Q) i j = ∑ k, blockB Q i k := by
    calc ∑ j, (blockB Q * Dinv * blockC Q) i j
        = ∑ j, ∑ k, (∑ l, blockB Q i l * Dinv l k) * blockC Q k j := by
          refine Finset.sum_congr rfl fun j _ => ?_
          simp [Matrix.mul_apply]
      _ = ∑ k, ∑ j, (∑ l, blockB Q i l * Dinv l k) * blockC Q k j := Finset.sum_comm
      _ = ∑ k, (∑ l, blockB Q i l * Dinv l k) * (∑ j, blockC Q k j) := by
          refine Finset.sum_congr rfl fun k _ => ?_
          rw [Finset.mul_sum]
      _ = ∑ k, ∑ l, blockB Q i l * Dinv l k * (∑ j, blockC Q k j) := by
          refine Finset.sum_congr rfl fun k _ => ?_
          rw [Finset.sum_mul]
      _ = ∑ l, ∑ k, blockB Q i l * Dinv l k * (∑ j, blockC Q k j) := Finset.sum_comm
      _ = ∑ l, blockB Q i l * (∑ k, Dinv l k * (∑ j, blockC Q k j)) := by
          refine Finset.sum_congr rfl fun l _ => ?_
          rw [Finset.mul_sum]
          exact Finset.sum_congr rfl fun k _ => by ring
      _ = ∑ l, blockB Q i l * 1 := by
          refine Finset.sum_congr rfl fun l _ => ?_
          rw [inner_row_sum Q Dinv hDinv l]
      _ = ∑ l, blockB Q i l := by simp
  have hA : ∑ j, traceV Q Dinv i j
      = (∑ j, blockA Q i j) + ∑ j, (blockB Q * Dinv * blockC Q) i j := by
    simp [traceV, Finset.sum_add_distrib]
  rw [hA, hBC]
  exact row_split_V Q i

/-! ## 4. Случай `h = 1`: точный обратный над `ℚ` -/

/-- Обратный к `I − D` при одном скрытом состоянии: `(1 − d)⁻¹`. -/
def inv1 (Q : StochMatrix (V ⊕ Fin 1)) : Matrix (Fin 1) (Fin 1) ℚ :=
  fun _ _ => (oneMinusD Q 0 0)⁻¹

theorem inv1_mul (Q : StochMatrix (V ⊕ Fin 1)) (h : oneMinusD Q 0 0 ≠ 0) :
    inv1 Q * oneMinusD Q = 1 := by
  ext i j
  fin_cases i
  fin_cases j
  simp only [Matrix.mul_apply, Fin.sum_univ_one, inv1]
  rw [Matrix.one_apply]
  simp only [if_true]
  field_simp

/-- След при `h = 1` — с сертифицированным обратным. -/
def traceV1 (Q : StochMatrix (V ⊕ Fin 1)) : Matrix V V ℚ := traceV Q (inv1 Q)

theorem traceV1_nonneg (Q : StochMatrix (V ⊕ Fin 1)) (_h : oneMinusD Q 0 0 ≠ 0)
    (hpos : 0 < oneMinusD Q 0 0) (i j : V) : 0 ≤ traceV1 Q i j := by
  refine traceV_nonneg Q (inv1 Q) (fun k l => ?_) i j
  have hk : k = 0 := Subsingleton.elim k 0
  have hl : l = 0 := Subsingleton.elim l 0
  subst hk; subst hl
  simp only [inv1]
  exact le_of_lt (inv_pos.mpr hpos)

theorem traceV1_row_sum (Q : StochMatrix (V ⊕ Fin 1)) (h : oneMinusD Q 0 0 ≠ 0)
    (i : V) : ∑ j, traceV1 Q i j = 1 :=
  traceV_row_sum Q (inv1 Q) (inv1_mul Q h) i

/-! ## 5. Связь со рядом Неймана (точное тождество с остатком)

Формула `(I−D)⁻¹ = Σ Dⁿ` **не** вводится как равенство: для произвольной `D`
ряд расходится. Вместо этого доказывается точное тождество с остатком при
`h = 1`, где сходимость обеспечена условием `0 ≤ d < 1`. -/

/-- Алгебраическая основа: `(1−d) · Σ_{n<N} dⁿ = 1 − d^N`. Без деления,
    поэтому верно при любом `d` и не требует `1 − d ≠ 0`. -/
theorem geom_mul (d : ℚ) (N : ℕ) :
    (1 - d) * ∑ n ∈ Finset.range N, d ^ n = 1 - d ^ N := by
  induction N with
  | zero => simp
  | succ N ih =>
    rw [Finset.sum_range_succ, mul_add, ih]
    ring

/-- `(1−d)⁻¹ = Σ_{n<N} dⁿ + d^N (1−d)⁻¹` — частичная сумма плюс остаток. -/
theorem geom_partial (d : ℚ) (hd : 1 - d ≠ 0) (N : ℕ) :
    (1 - d)⁻¹ = ∑ n ∈ Finset.range N, d ^ n + d ^ N * (1 - d)⁻¹ := by
  have hS : (1 - d) * (∑ n ∈ Finset.range N, d ^ n) = 1 - d ^ N := geom_mul d N
  have hsum : (∑ n ∈ Finset.range N, d ^ n) = (1 - d)⁻¹ * (1 - d ^ N) := by
    rw [← hS, ← mul_assoc, inv_mul_cancel₀ hd, one_mul]
  rw [hsum, mul_sub, mul_one]
  ring

/-- Если `d^N = 0`, ряд обрывается: остаток равен нулю, и след точно равен
    частичной сумме. Это единственный случай, когда `(I−D)⁻¹ = Σ Dⁿ`
    доказывается как **равенство**, а не как предел. -/
theorem geom_terminates (d : ℚ) (hd : 1 - d ≠ 0) (N : ℕ) (hN : d ^ N = 0) :
    (1 - d)⁻¹ = ∑ n ∈ Finset.range N, d ^ n := by
  rw [geom_partial d hd N, hN, zero_mul, add_zero]

/-! ## 6. Граница: поглощающий скрытый класс `D = I` -/

/-- При `D = I` обратного к `I − D` не существует: `0 * X = 0 ≠ 1`.
    Никакой «нормировки по умолчанию» быть не может. -/
theorem absorbing_no_inverse [Nonempty H] (X : Matrix H H ℚ) :
    ¬ ((1 - (1 : Matrix H H ℚ)) * X = 1) := by
  intro hcontra
  have h0 : (0 : Matrix H H ℚ) = 1 := by simpa using hcontra
  have a := Classical.arbitrary H
  have hentry : (0 : ℚ) = 1 := by
    have := congrFun (congrFun h0 a) a
    simpa using this
  exact zero_ne_one hentry

/-- Наивный след `A + B·0·C = A` субстохастичен, если из наблюдаемого
    состояния есть переход в скрытое. Это и есть «частичный след»:
    его **нельзя** молча нормировать. -/
theorem absorbing_gives_substochastic (Q : StochMatrix (V ⊕ H))
    (h : ∃ i : V, 0 < ∑ k, blockB Q i k) :
    ∃ i : V, ∑ j, traceV Q 0 i j < 1 := by
  obtain ⟨i, hi⟩ := h
  refine ⟨i, ?_⟩
  have hzero : ∑ j, traceV Q 0 i j = ∑ j, blockA Q i j := by
    simp [traceV, Matrix.mul_zero, Matrix.zero_mul]
  rw [hzero]
  have := row_split_V Q i
  linarith

/-! ## 7. Точные фикстуры

### 7.1 `Q_RGB` — три состояния, `V = {R,G}`, `H = {B}`

```
Q_RGB = [[1/5,  3/10, 1/2],
         [1/2,  1/10, 2/5],
         [2/5,  1/2,  1/10]]
```

Ожидаемый след: `[[19/45, 26/45], [61/90, 29/90]]`.
(Значения сверены с независимым расчётом в точных дробях; см. `CORRESPONDENCE.md`,
раздел SOURCE_NOTE.) -/

/-- Матрица `Q_RGB` на разбиении `Fin 2 ⊕ Fin 1`. -/
def QRGBmat : (Fin 2 ⊕ Fin 1) → (Fin 2 ⊕ Fin 1) → ℚ
  | Sum.inl i, Sum.inl j => ![![1 / 5, 3 / 10], ![1 / 2, 1 / 10]] i j
  | Sum.inl i, Sum.inr _ => ![1 / 2, 2 / 5] i
  | Sum.inr _, Sum.inl j => ![2 / 5, 1 / 2] j
  | Sum.inr _, Sum.inr _ => 1 / 10

def QRGB : StochMatrix (Fin 2 ⊕ Fin 1) where
  toMatrix := QRGBmat
  nonneg p q := by
    rcases p with i | k
    · rcases q with j | l
      · fin_cases i <;> fin_cases j <;> simp [QRGBmat] <;> norm_num
      · fin_cases i <;> simp [QRGBmat] <;> norm_num
    · rcases q with j | l
      · fin_cases j <;> simp [QRGBmat] <;> norm_num
      · simp [QRGBmat] <;> norm_num
  row_sum p := by
    rcases p with i | k
    · rw [Fintype.sum_sum_type]
      fin_cases i <;> simp [QRGBmat, Fin.sum_univ_two, Fin.sum_univ_one] <;> norm_num
    · rw [Fintype.sum_sum_type]
      simp [QRGBmat, Fin.sum_univ_two, Fin.sum_univ_one] <;> norm_num

/-- `I − D` для `Q_RGB`: `1 − 1/10 = 9/10 ≠ 0`, поэтому обратный существует. -/
theorem QRGB_invertible : oneMinusD QRGB 0 0 ≠ 0 := by
  simp [oneMinusD, blockD, QRGB, QRGBmat]
  norm_num

/-- **Точный след `Q_RGB`.** Четыре элемента, покомпонентно. -/
theorem QRGB_trace :
    traceV1 QRGB 0 0 = 19 / 45 ∧ traceV1 QRGB 0 1 = 26 / 45 ∧
    traceV1 QRGB 1 0 = 61 / 90 ∧ traceV1 QRGB 1 1 = 29 / 90 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    norm_num [traceV1, traceV, blockA, blockB, blockC, blockD, oneMinusD, inv1,
      QRGB, QRGBmat, Matrix.mul_apply, Matrix.add_apply, Fin.sum_univ_one,
      Fin.sum_univ_two]

/-- След снова стохастичен — проверка условия возврата на конкретных числах. -/
theorem QRGB_trace_row_sums (i : Fin 2) : ∑ j, traceV1 QRGB i j = 1 :=
  traceV1_row_sum QRGB QRGB_invertible i

/-! ### 7.2 `Q4` — равномерная на четырёх состояниях, `V = {0,1,2}`, `H = {3}`

Ожидаемый след: все элементы `1/3`. -/

/-- Равномерное ядро на `Fin 3 ⊕ Fin 1` (все элементы `1/4`). -/
def Q4T : StochMatrix (Fin 3 ⊕ Fin 1) where
  toMatrix := fun _ _ => 1 / 4
  nonneg i j := by norm_num
  row_sum p := by
    rw [Fintype.sum_sum_type]
    simp [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
    norm_num

theorem Q4T_invertible : oneMinusD Q4T 0 0 ≠ 0 := by
  simp [oneMinusD, blockD, Q4T]
  norm_num

/-- **Точный след `Q4`:** все элементы `1/3`. -/
theorem Q4T_trace (i j : Fin 3) : traceV1 Q4T i j = 1 / 3 := by
  norm_num [traceV1, traceV, blockA, blockB, blockC, blockD, oneMinusD, inv1,
    Q4T, Matrix.mul_apply, Matrix.add_apply, Fin.sum_univ_one, Fin.sum_univ_three]

/-- `π(V) = 3/4`, следовательно отношение событийных часов Каца равно `4/3`.
    Это **условное** утверждение: оно требует стационарности и положительной
    возвратности, которые здесь не доказываются. -/
theorem Q4T_kac_ratio : (1 : ℚ) / (3 / 4) = 4 / 3 := by norm_num

end Bridge
end QCat
