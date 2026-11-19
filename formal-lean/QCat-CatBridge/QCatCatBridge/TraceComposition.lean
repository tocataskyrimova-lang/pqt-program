/-
  QCAT-CAT-BRIDGE-001 · M3 — TRACE COMPOSITION: WHAT DOES NOT FUNCTORIALIZE
  =========================================================================

  Три пункта контракта:

  1. Точный контрпример: `Tr(P·R) ≠ Tr(P)·Tr(R)`. Доказан полностью,
     с явными матрицами (не только булевым «не равно»).
  2. Yanking для чистого свопа `[[0,I],[I,0]]`. Доказан полностью.
  3. Башня `Tr_{V2}(Tr_{V1}(Q)) = Tr_{V2}(Q)` при `V2 ⊆ V1`.
     **Статус: OPEN.** Точная формулировка и минимальная недостающая лемма
     («Schur complement of Schur complement», блочный обратный `2×2`)
     зафиксированы в `CORRESPONDENCE.md`, раздел M3.
     Это осознанно не выдаётся за доказательство.

  ВАЖНО (п.3 контракта): закон yanking САМ ПО СЕБЕ **не** даёт
  traced-моноидальную структуру Джояла–Стрита–ВерITY. Здесь нет ни
  dinaturality, ни vanishing I/II, ни superposing, ни замкнутости области
  допустимого feedback по композиции и тензору. Поэтому `Traced`-структура
  не объявляется.
-/
import QCatCatBridge.PhaseObservation

open scoped BigOperators

namespace QCat
namespace Bridge

open StochMatrix

/-! ## 1. Контрпример на три состояния

`V = {0,1}`, `H = {2}`; `P` меняет `0 ↔ 2`, `R` меняет `1 ↔ 2`.

Оба следа равны `I₂`, но след произведения — `swap₂`. Значит `Tr` не
функториален. -/

/-- `P`: перестановка `0 ↔ 2` (в `V ⊕ H`: `inl 0 ↔ inr 0`), состояние 1 на месте. -/
def Pmat : (Fin 2 ⊕ Fin 1) → (Fin 2 ⊕ Fin 1) → ℚ
  | Sum.inl i, Sum.inl j => if i = 1 ∧ j = 1 then 1 else 0
  | Sum.inl i, Sum.inr _ => if i = 0 then 1 else 0
  | Sum.inr _, Sum.inl j => if j = 0 then 1 else 0
  | Sum.inr _, Sum.inr _ => 0

/-- `R`: перестановка `1 ↔ 2`, состояние 0 на месте. -/
def Rmat : (Fin 2 ⊕ Fin 1) → (Fin 2 ⊕ Fin 1) → ℚ
  | Sum.inl i, Sum.inl j => if i = 0 ∧ j = 0 then 1 else 0
  | Sum.inl i, Sum.inr _ => if i = 1 then 1 else 0
  | Sum.inr _, Sum.inl j => if j = 1 then 1 else 0
  | Sum.inr _, Sum.inr _ => 0

theorem Pmat_nonneg (p q : Fin 2 ⊕ Fin 1) : 0 ≤ Pmat p q := by
  rcases p with i | k <;> rcases q with j | l
  · dsimp only [Pmat]; split <;> norm_num
  · dsimp only [Pmat]; norm_num; split <;> norm_num
  · dsimp only [Pmat]; split <;> norm_num
  · dsimp only [Pmat]; norm_num

theorem Rmat_nonneg (p q : Fin 2 ⊕ Fin 1) : 0 ≤ Rmat p q := by
  rcases p with i | k <;> rcases q with j | l
  · dsimp only [Rmat]; split <;> norm_num
  · dsimp only [Rmat]; norm_num; split <;> norm_num
  · dsimp only [Rmat]; split <;> norm_num
  · dsimp only [Rmat]; norm_num

theorem Pmat_row_sum (p : Fin 2 ⊕ Fin 1) : ∑ q, Pmat p q = 1 := by
  rcases p with i | k
  · rw [Fintype.sum_sum_type]
    fin_cases i <;> simp [Pmat, Fin.sum_univ_two, Fin.sum_univ_one]
  · rw [Fintype.sum_sum_type]
    simp [Pmat, Fin.sum_univ_two, Fin.sum_univ_one]

theorem Rmat_row_sum (p : Fin 2 ⊕ Fin 1) : ∑ q, Rmat p q = 1 := by
  rcases p with i | k
  · rw [Fintype.sum_sum_type]
    fin_cases i <;> simp [Rmat, Fin.sum_univ_two, Fin.sum_univ_one]
  · rw [Fintype.sum_sum_type]
    simp [Rmat, Fin.sum_univ_two, Fin.sum_univ_one]

def P : StochMatrix (Fin 2 ⊕ Fin 1) where
  toMatrix := Pmat
  nonneg := Pmat_nonneg
  row_sum := Pmat_row_sum

def R : StochMatrix (Fin 2 ⊕ Fin 1) where
  toMatrix := Rmat
  nonneg := Rmat_nonneg
  row_sum := Rmat_row_sum

/-- Скрытое состояние в обоих случаях не переходит в себя: `D = 0`,
    поэтому `(I−D)⁻¹ = 1` и след сертифицирован тривиально. -/
theorem P_invertible : oneMinusD P 0 0 ≠ 0 := by
  simp [oneMinusD, blockD, P, Pmat]

theorem R_invertible : oneMinusD R 0 0 ≠ 0 := by
  simp [oneMinusD, blockD, R, Rmat]

/-- `Tr(P) = I₂` — **значения**, а не булево утверждение. -/
theorem TrP_values :
    traceV1 P 0 0 = 1 ∧ traceV1 P 0 1 = 0 ∧
    traceV1 P 1 0 = 0 ∧ traceV1 P 1 1 = 1 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    norm_num [traceV1, traceV, blockA, blockB, blockC, blockD, oneMinusD, inv1,
      P, Pmat, Matrix.mul_apply, Matrix.add_apply, Fin.sum_univ_one, Fin.sum_univ_two]

/-- `Tr(R) = I₂`. -/
theorem TrR_values :
    traceV1 R 0 0 = 1 ∧ traceV1 R 0 1 = 0 ∧
    traceV1 R 1 0 = 0 ∧ traceV1 R 1 1 = 1 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    norm_num [traceV1, traceV, blockA, blockB, blockC, blockD, oneMinusD, inv1,
      R, Rmat, Matrix.mul_apply, Matrix.add_apply, Fin.sum_univ_one, Fin.sum_univ_two]

/-- `Tr(P·R) = swap₂` — **значения**. Порядок произведения: `P * R`
    означает «сначала `P`, затем `R`» (row-vector, п.1 контракта). -/
theorem TrPR_values :
    traceV1 (P * R) 0 0 = 0 ∧ traceV1 (P * R) 0 1 = 1 ∧
    traceV1 (P * R) 1 0 = 1 ∧ traceV1 (P * R) 1 1 = 0 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    norm_num [traceV1, traceV, blockA, blockB, blockC, blockD, oneMinusD, inv1,
      P, R, Pmat, Rmat, Matrix.mul_apply, Matrix.add_apply, Fin.sum_univ_one,
      Fin.sum_univ_two]

/-- **Нефункториальность.** `Tr(P·R) ≠ Tr(P)·Tr(R)`. -/
theorem trace_not_functorial : traceV1 (P * R) ≠ traceV1 P * traceV1 R := by
  intro h
  have h00 : traceV1 (P * R) 0 0 = (traceV1 P * traceV1 R) 0 0 := by rw [h]
  have hR : traceV1 R = 1 := by
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [TrR_values, Matrix.one_apply]
  have hP : traceV1 P = 1 := by
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [TrP_values, Matrix.one_apply]
  rw [hR, hP, Matrix.mul_one] at h00
  have h0 : traceV1 (P * R) 0 0 = 0 := TrPR_values.1
  rw [h0] at h00
  have : (1 : ℚ) = 0 := by simpa using h00.symm
  exact one_ne_zero this

/-! ## 2. Yanking для чистого свопа

`Q = [[0, I], [I, 0]]` на `α ⊕ α`: «сначала в скрытую часть, потом обратно».
Тогда `D = 0`, `(I−D)⁻¹ = 1`, и `Tr_V(Q) = 0 + I·1·I = I`.

Это ровно yanking для петли обратной связи. **Но** это только один закон:
он не даёт traced-моноидальную структуру. -/

/-- Матрица чистого свопа `[[0,I],[I,0]]`: `inl a ↦ inr a`, `inr b ↦ inl b`. -/
def swapMat (α : Type*) [DecidableEq α] : (α ⊕ α) → (α ⊕ α) → ℚ
  | Sum.inl a, Sum.inr b => if a = b then 1 else 0
  | Sum.inr b, Sum.inl a => if b = a then 1 else 0
  | _, _ => 0

/-- Чистый своп как стохастическая матрица. -/
def swapBlock (α : Type*) [Fintype α] [DecidableEq α] : StochMatrix (α ⊕ α) where
  toMatrix := swapMat α
  nonneg p q := by
    rcases p with a | b <;> rcases q with c | d
    · simp [swapMat]
    · simp only [swapMat]; split <;> norm_num
    · simp only [swapMat]; split <;> norm_num
    · simp [swapMat]
  row_sum p := by
    rcases p with a | b
    · rw [Fintype.sum_sum_type]
      simp [swapMat]
    · rw [Fintype.sum_sum_type]
      simp [swapMat]

/-- Блоки чистого свопа: `A = 0`, `B = C = I`, `D = 0`. -/
theorem swapBlock_blockA (α : Type*) [Fintype α] [DecidableEq α] :
    blockA (swapBlock α) = 0 := by
  ext i j
  rfl

theorem swapBlock_blockB (α : Type*) [Fintype α] [DecidableEq α] :
    blockB (swapBlock α) = 1 := by
  ext i k
  rfl

theorem swapBlock_blockC (α : Type*) [Fintype α] [DecidableEq α] :
    blockC (swapBlock α) = 1 := by
  ext k j
  rfl

theorem swapBlock_blockD (α : Type*) [Fintype α] [DecidableEq α] :
    blockD (swapBlock α) = 0 := by
  ext k l
  rfl

/-- **Yanking.** След чистого свопа — единица на наблюдаемой части.
    `Tr = A + B·1·C = 0 + I·I = I`. -/
theorem yanking (α : Type*) [Fintype α] [DecidableEq α] :
    traceV (swapBlock α) 1 = 1 := by
  rw [traceV, swapBlock_blockA α, swapBlock_blockB α, swapBlock_blockC α]
  simp

end Bridge
end QCat
