/-
  QCAT-CAT-BRIDGE-001 · ADDENDUM-002 / H2 — ЗНАКОВАЯ РЕАЛИЗАЦИЯ
  ==============================================================

  ЭКСПЕРИМЕНТ, А НЕ ФИЗИЧЕСКИЙ ЗАКОН.

  `G = {±1} × {±1}`, кодировка `0 ↦ +1`, `1 ↦ −1`. Для `g = (a,b)`:

  ```
  p_stay(g) = ((a + b)/2)²        p_flip(g) = ((a − b)/2)²
  M(g)      = [[p_stay, p_flip],
               [p_flip, p_stay]]
  ```

  ЧТО ДОКАЗАНО (пункты (i)–(iv) аддендума):
  * (i)   `M(g)` стохастическая и перестановочная (`Mmat_row_sum`,
          `Mmat_nonneg`, `Mmat_perm`, `Mstoch`);
  * (ii)  `M(1,1) = I₂` (`Mmat_gPlus`), `M(1,−1) = swap₂` (`Mmat_gMixed`);
  * (iii) `M(g·h) = M(g)·M(h)` на `G` (`Mmat_mul`, `Mstoch_mul`);
  * (iv)  ядро в единице — ровно диагональ `{(1,1), (−1,−1)}`
          (`Mmat_kernel_at_one`), т.е. общее изменение знака теряется
          (`Mmat_global_sign_blind`, `Mmat_not_injective`).

  ЧЕГО ЗДЕСЬ НЕТ (прямо запрещено аддендумом):
  * это **не** каноническое правило Борна и не «фаза → вероятность»;
  * это **не** контрпример к узкому no-go `stochastic_phase_forces_one`:
    там речь о прямой реализации `ω · swap` с единственным фазовым весом
    в строке, здесь — о **неверной** (nonfaithful) реализации ограниченной
    знаковой группы;
  * `M` теряет ровно ту информацию, которую обязана терять: `M(g)` зависит
    только от произведения `a·b`, поэтому глобальная смена знака невидима.
-/
import QCatCatBridge.MarkovKernel

open scoped BigOperators

namespace QCat
namespace Bridge

/-! ## 1. Группа знаков -/

/-- `G = {±1} × {±1}` в кодировке `0 ↦ +1`, `1 ↦ −1`.
Сложение в `Fin 2` соответствует умножению знаков. -/
abbrev G : Type := Fin 2 × Fin 2

/-- Кодировка знака: `sgn 0 = 1`, `sgn 1 = −1`. -/
def sgn : Fin 2 → ℚ := ![1, -1]

@[simp] theorem sgn_zero : sgn 0 = 1 := rfl
@[simp] theorem sgn_one : sgn 1 = -1 := rfl

theorem sgn_sq (i : Fin 2) : sgn i ^ 2 = 1 := by
  fin_cases i <;> norm_num [sgn]

/-- `(1,1)` — обе компоненты `+1`. -/
def gPlus : G := ((0 : Fin 2), (0 : Fin 2))

/-- `(1,−1)` — смешанные знаки. -/
def gMixed : G := ((0 : Fin 2), (1 : Fin 2))

/-- `(−1,−1)` — глобальная смена знака. -/
def gNegAll : G := ((1 : Fin 2), (1 : Fin 2))

/-! ## 2. Вероятности и матрица -/

/-- `p_stay = ((a+b)/2)²`. -/
def pStay (g : G) : ℚ := ((sgn g.1 + sgn g.2) / 2) ^ 2

/-- `p_flip = ((a−b)/2)²`. -/
def pFlip (g : G) : ℚ := ((sgn g.1 - sgn g.2) / 2) ^ 2

/-- `swap₂ = [[0,1],[1,0]]`. -/
def Mswap : Matrix (Fin 2) (Fin 2) ℚ := ![![0, 1], ![1, 0]]

/-- `M(g) = [[p_stay, p_flip],[p_flip, p_stay]]`. -/
def Mmat (g : G) : Matrix (Fin 2) (Fin 2) ℚ :=
  ![![pStay g, pFlip g], ![pFlip g, pStay g]]

@[simp] theorem Mmat_zero_zero (g : G) : Mmat g 0 0 = pStay g := rfl
@[simp] theorem Mmat_zero_one (g : G) : Mmat g 0 1 = pFlip g := rfl
@[simp] theorem Mmat_one_zero (g : G) : Mmat g 1 0 = pFlip g := rfl
@[simp] theorem Mmat_one_one (g : G) : Mmat g 1 1 = pStay g := rfl

theorem pStay_nonneg (g : G) : 0 ≤ pStay g := sq_nonneg _

theorem pFlip_nonneg (g : G) : 0 ≤ pFlip g := sq_nonneg _

/-- `p_stay + p_flip = 1`: сумма квадратов половин разности и суммы. -/
theorem pStay_add_pFlip (g : G) : pStay g + pFlip g = 1 := by
  have h1 : sgn g.1 ^ 2 = 1 := sgn_sq g.1
  have h2 : sgn g.2 ^ 2 = 1 := sgn_sq g.2
  have hcalc : ((sgn g.1 + sgn g.2) / 2) ^ 2 + ((sgn g.1 - sgn g.2) / 2) ^ 2
      = (sgn g.1 ^ 2 + sgn g.2 ^ 2) / 2 := by ring
  simp only [pStay, pFlip]
  rw [hcalc, h1, h2]
  norm_num

/-- Обратный порядок суммы — нужен для строки `1`. -/
theorem pFlip_add_pStay (g : G) : pFlip g + pStay g = 1 := by
  rw [add_comm]
  exact pStay_add_pFlip g

/-! ## 3. Свёртка: `M(g)` зависит только от произведения знаков

Это ключ ко всем пунктам: `p_stay = 1, p_flip = 0` при равных знаках и
`p_stay = 0, p_flip = 1` при разных. -/

theorem sgn_add_eq_zero_of_ne {i j : Fin 2} (h : i ≠ j) : sgn i + sgn j = 0 := by
  fin_cases i <;> fin_cases j <;> simp_all [sgn]

theorem pStay_eq_one_of_eq {g : G} (h : g.1 = g.2) : pStay g = 1 := by
  have hs : sgn g.1 = sgn g.2 := by rw [h]
  have h2 : sgn g.1 ^ 2 = 1 := sgn_sq g.1
  have hcalc : (sgn g.1 + sgn g.2) / 2 = sgn g.1 := by rw [hs]; ring
  simp only [pStay]
  rw [hcalc, h2]

theorem pFlip_eq_zero_of_eq {g : G} (h : g.1 = g.2) : pFlip g = 0 := by
  have hs : sgn g.1 = sgn g.2 := by rw [h]
  have hcalc : (sgn g.1 - sgn g.2) / 2 = 0 := by rw [hs]; ring
  simp only [pFlip]
  rw [hcalc]
  norm_num

theorem pStay_eq_zero_of_ne {g : G} (h : g.1 ≠ g.2) : pStay g = 0 := by
  have hs : sgn g.1 + sgn g.2 = 0 := sgn_add_eq_zero_of_ne h
  simp only [pStay]
  rw [hs]
  norm_num

theorem pFlip_eq_one_of_ne {g : G} (h : g.1 ≠ g.2) : pFlip g = 1 := by
  have hs : sgn g.1 + sgn g.2 = 0 := sgn_add_eq_zero_of_ne h
  have hs2 : sgn g.2 = -sgn g.1 := by linarith
  have h2 : sgn g.1 ^ 2 = 1 := sgn_sq g.1
  have hcalc : (sgn g.1 - sgn g.2) / 2 = sgn g.1 := by rw [hs2]; ring
  simp only [pFlip]
  rw [hcalc, h2]

/-- **Свёртка.** `M(g)` — либо единица, либо своп: третьего нет.
Это и есть причина потери знака. -/
theorem Mmat_iff (g : G) :
    Mmat g = if g.1 = g.2 then (1 : Matrix (Fin 2) (Fin 2) ℚ) else Mswap := by
  by_cases h : g.1 = g.2
  · rw [if_pos h]
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [Mmat, Mswap, Matrix.one_apply, pStay_eq_one_of_eq h, pFlip_eq_zero_of_eq h]
  · rw [if_neg h]
    ext i j
    fin_cases i <;> fin_cases j <;>
      simp [Mmat, Mswap, pStay_eq_zero_of_ne h, pFlip_eq_one_of_ne h]

/-! ## 4. (i) Стохастичность и перестановочность -/

theorem Mmat_row_sum (g : G) (i : Fin 2) : ∑ j, Mmat g i j = 1 := by
  fin_cases i <;> simp [Fin.sum_univ_two, pStay_add_pFlip, pFlip_add_pStay]

theorem Mmat_perm (g : G) (i j : Fin 2) : Mmat g i j = 0 ∨ Mmat g i j = 1 := by
  rw [Mmat_iff]
  by_cases h : g.1 = g.2
  · rw [if_pos h]
    fin_cases i <;> fin_cases j <;> simp [Matrix.one_apply]
  · rw [if_neg h]
    fin_cases i <;> fin_cases j <;> simp [Mswap]

theorem Mmat_nonneg (g : G) (i j : Fin 2) : 0 ≤ Mmat g i j := by
  rcases Mmat_perm g i j with h | h <;> rw [h] <;> norm_num

/-- `M(g)` как элемент `StochMatrix (Fin 2)` — переиспользует M1. -/
def Mstoch (g : G) : StochMatrix (Fin 2) where
  toMatrix := Mmat g
  nonneg := Mmat_nonneg g
  row_sum := Mmat_row_sum g

theorem Mstoch_apply (g : G) (i j : Fin 2) : Mstoch g i j = Mmat g i j := rfl

/-! ## 5. (ii) Образующие -/

theorem Mmat_gPlus : Mmat gPlus = 1 := by
  rw [Mmat_iff]
  simp [gPlus]

theorem Mmat_gMixed : Mmat gMixed = Mswap := by
  rw [Mmat_iff]
  have h : ¬ (gMixed.1 = gMixed.2) := by decide
  rw [if_neg h]

theorem Mmat_gNegAll : Mmat gNegAll = 1 := by
  rw [Mmat_iff]
  simp [gNegAll]

theorem Mstoch_gPlus : Mstoch gPlus = 1 := by
  apply StochMatrix.ext
  exact Mmat_gPlus

/-! ## 6. (iii) Мультипликативность

`g + h` — покомпонентное сложение в `Fin 2`, что и есть умножение знаков. -/

theorem add_fst_eq_snd_iff (g h : G) :
    (g + h).1 = (g + h).2 ↔ (g.1 = g.2 ↔ h.1 = h.2) := by
  obtain ⟨g1, g2⟩ := g
  obtain ⟨h1, h2⟩ := h
  fin_cases g1 <;> fin_cases g2 <;> fin_cases h1 <;> fin_cases h2 <;> decide

theorem Mswap_mul_self : Mswap * Mswap = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Mswap, Matrix.mul_apply, Fin.sum_univ_two, Matrix.one_apply]

/-- **Мультипликативность.** `M(g + h) = M(g) · M(h)` для всех `g, h ∈ G`. -/
theorem Mmat_mul (g h : G) : Mmat (g + h) = Mmat g * Mmat h := by
  rw [Mmat_iff, Mmat_iff, Mmat_iff]
  by_cases hg : g.1 = g.2 <;> by_cases hh : h.1 = h.2
  · have hgh : (g + h).1 = (g + h).2 :=
      (add_fst_eq_snd_iff g h).mpr ⟨fun _ => hh, fun _ => hg⟩
    rw [if_pos hgh, if_pos hg, if_pos hh, Matrix.mul_one]
  · have hgh : ¬ ((g + h).1 = (g + h).2) :=
      fun hc => hh (((add_fst_eq_snd_iff g h).mp hc).mp hg)
    rw [if_neg hgh, if_pos hg, if_neg hh, Matrix.one_mul]
  · have hgh : ¬ ((g + h).1 = (g + h).2) :=
      fun hc => hg (((add_fst_eq_snd_iff g h).mp hc).mpr hh)
    rw [if_neg hgh, if_neg hg, if_pos hh, Matrix.mul_one]
  · have hgh : (g + h).1 = (g + h).2 :=
      (add_fst_eq_snd_iff g h).mpr ⟨fun hc => absurd hc hg, fun hc => absurd hc hh⟩
    rw [if_pos hgh, if_neg hg, if_neg hh, Mswap_mul_self]

theorem Mstoch_mul (g h : G) : Mstoch (g + h) = Mstoch g * Mstoch h := by
  apply StochMatrix.ext
  exact Mmat_mul g h

/-! ## 7. (iv) Ядро: глобальная смена знака теряется -/

/-- **Ядро в единице — ровно диагональ.** `M(g) = I₂ ⇔ g₁ = g₂`,
т.е. `g ∈ {(1,1), (−1,−1)}`. -/
theorem Mmat_kernel_at_one (g : G) : Mmat g = Mmat gPlus ↔ g.1 = g.2 := by
  rw [Mmat_gPlus, Mmat_iff]
  by_cases h : g.1 = g.2
  · rw [if_pos h]
    exact ⟨fun _ => h, fun _ => rfl⟩
  · rw [if_neg h]
    constructor
    · intro hc
      have hentry : Mswap (0 : Fin 2) (1 : Fin 2)
          = (1 : Matrix (Fin 2) (Fin 2) ℚ) (0 : Fin 2) (1 : Fin 2) := by rw [hc]
      simp [Mswap, Matrix.one_apply] at hentry
    · intro hc
      exact absurd hc h

/-- **Общее изменение знака невидимо.** `M(g·(−1,−1)) = M(g)`. -/
theorem Mmat_global_sign_blind (g : G) : Mmat (g + gNegAll) = Mmat g := by
  rw [Mmat_iff, Mmat_iff]
  have hiff : (g + gNegAll).1 = (g + gNegAll).2 ↔ g.1 = g.2 := by
    rw [add_fst_eq_snd_iff]
    simp [gNegAll]
  by_cases h : g.1 = g.2
  · rw [if_pos (hiff.mpr h), if_pos h]
  · rw [if_neg (fun hc => h (hiff.mp hc)), if_neg h]

/-- **`M` не инъективна.** Свидетели: `(1,1) ≠ (−1,−1)`, но образы совпадают. -/
theorem Mmat_not_injective : ¬ Function.Injective Mmat := by
  intro hinj
  have heq : gPlus = gNegAll := hinj (by rw [Mmat_gPlus, Mmat_gNegAll])
  have hfst : ((0 : Fin 2) = (1 : Fin 2)) := congrArg Prod.fst heq
  exact absurd hfst (by decide)

/-- **Сводный сертификат H2.** Все четыре пункта аддендума в одной теореме. -/
theorem sign_realization_summary :
    (∀ (g : G) (i : Fin 2), ∑ j, Mmat g i j = 1) ∧
    (∀ (g : G) (i j : Fin 2), 0 ≤ Mmat g i j) ∧
    (∀ (g : G) (i j : Fin 2), Mmat g i j = 0 ∨ Mmat g i j = 1) ∧
    Mmat gPlus = 1 ∧
    Mmat gMixed = Mswap ∧
    (∀ g h : G, Mmat (g + h) = Mmat g * Mmat h) ∧
    (∀ g : G, Mmat (g + gNegAll) = Mmat g) ∧
    ¬ Function.Injective Mmat :=
  ⟨Mmat_row_sum, Mmat_nonneg, Mmat_perm, Mmat_gPlus, Mmat_gMixed, Mmat_mul,
    Mmat_global_sign_blind, Mmat_not_injective⟩

end Bridge
end QCat
