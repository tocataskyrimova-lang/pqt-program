/-
  QCAT-CAT-BRIDGE-001 · M4 — PHASE OBSERVATION
  ============================================

  `R = Q₋₁ ≃ ℚ × ℚ` (расщепляемые комплексные числа): `e₊ = (1,0)`,
  `e₋ = (0,1)`, `ι = (1,−1)`, `ι² = 1`.

  Проекция наблюдения: `Π_λ(a,b) = λa + (1−λ)b`, `0 ≤ λ ≤ 1`.

  ЧТО ДОКАЗАНО:
  * точный критерий видимости `Π_λ(uω₁) = Π_λ(uω₂)`;
  * для `u = e₊`, `ω₁ = 1`, `ω₂ = ι` выходы совпадают при **любом** `λ`
    (потерянный сектор не восстанавливается никакой выпуклой смесью);
  * `Π_λ` **не** мультипликативна при `0 < λ < 1`;
  * выпуклая смесь двух стохастических каналов снова стохастична;
  * **H1 (ADDENDUM-002):** точный дефект `Π_λ(z·w) − Π_λ(z)Π_λ(w) =
    λ(1−λ)(z₊−z₋)(w₊−w₋)` и эквивалентность «мультипликативна ⇔ λ ∈ {0,1}»;
  * **H3-замечание:** умножение на `u` инъективно ⇔ `u₊ ≠ 0 ∧ u₋ ≠ 0`.

  ЧТО НЕ УТВЕРЖДАЕТСЯ (прямо запрещено контрактом):
  * `e₋` **не** объявляется «стерильным физическим сектором»;
  * отрицательные фазовые значения **не** трактуются как вероятности;
  * отображение «фаза → вероятность» (модуль-квадрат, измерение) здесь
    **не** вводится: для него нужны отдельные правила и обязательства.
-/
import QCatCatBridge.ObserverTrace

open scoped BigOperators

namespace QCat
namespace Bridge

/-! ## 1. Расщепляемые комплексные числа -/

/-- `R = Q₋₁ ≈ ℚ × ℚ`. -/
abbrev SC := ℚ × ℚ

/-- Единица фазы: `1 = (1,1)`. -/
def scOne : SC := (1, 1)

/-- `e₊ = (1,0)`. -/
def eplus : SC := (1, 0)

/-- `e₋ = (0,1)`. -/
def eminus : SC := (0, 1)

/-- `ι = (1,−1)`, `ι² = 1`. -/
def iota : SC := (1, -1)

/-- Покомпонентное умножение (это и есть умножение в `Q₋₁`). -/
def mulSC (a b : SC) : SC := (a.1 * b.1, a.2 * b.2)

@[simp] theorem mulSC_fst (a b : SC) : (mulSC a b).1 = a.1 * b.1 := rfl
@[simp] theorem mulSC_snd (a b : SC) : (mulSC a b).2 = a.2 * b.2 := rfl

/-- Неотрицательный конус — покомпонентный. -/
def cone (a : SC) : Prop := 0 ≤ a.1 ∧ 0 ≤ a.2

theorem iota_sq : mulSC iota iota = scOne := by
  simp [mulSC, iota, scOne]

theorem eplus_mul_eminus : mulSC eplus eminus = (0, 0) := by
  simp [mulSC, eplus, eminus]

/-- `e₊` и `e₋` — делители нуля; именно это ломает мультипликативность
    проекции ниже. -/
theorem zero_divisors : eplus ≠ (0, 0) ∧ eminus ≠ (0, 0) ∧ mulSC eplus eminus = (0, 0) := by
  refine ⟨?_, ?_, eplus_mul_eminus⟩
  · intro h
    have h1 : (1 : ℚ) = 0 := by simpa [eplus] using congrArg Prod.fst h
    exact one_ne_zero h1
  · intro h
    have h1 : (1 : ℚ) = 0 := by simpa [eminus] using congrArg Prod.snd h
    exact one_ne_zero h1

/-- `ι` лежит вне неотрицательного конуса: это **не** вероятность. -/
theorem iota_not_cone : ¬ cone iota := by
  intro h
  have h2 : (0 : ℚ) ≤ -1 := h.2
  linarith

/-! ## 2. Проекция наблюдения -/

/-- `Π_λ(a,b) = λa + (1−λ)b`. -/
def Pi (lam : ℚ) (a : SC) : ℚ := lam * a.1 + (1 - lam) * a.2

/-- **Точный критерий видимости.** Два фазовых произведения дают одинаковый
    наблюдаемый выход тогда и только тогда, когда их разность лежит в ядре
    проекции. Это эквивалентность, а не следствие. -/
theorem visibility_iff (lam : ℚ) (u ω1 ω2 : SC) :
    Pi lam (mulSC u ω1) = Pi lam (mulSC u ω2) ↔
      lam * (u.1 * (ω1.1 - ω2.1)) + (1 - lam) * (u.2 * (ω1.2 - ω2.2)) = 0 := by
  simp only [Pi, mulSC_fst, mulSC_snd]
  constructor <;> intro h <;> linarith

/-- **Ключевой случай контракта.** При `u = e₊`, `ω₁ = 1`, `ω₂ = ι` выходы
    совпадают при любом `λ`: сектор `e₋` полностью стёрт проекцией. -/
theorem eplus_blind (lam : ℚ) :
    Pi lam (mulSC eplus scOne) = Pi lam (mulSC eplus iota) := by
  simp [Pi, mulSC, eplus, scOne, iota]

/-- То же в форме критерия: разность равна нулю тождественно по `λ`. -/
theorem eplus_blind_criterion (lam : ℚ) :
    lam * (eplus.1 * (scOne.1 - iota.1)) + (1 - lam) * (eplus.2 * (scOne.2 - iota.2)) = 0 := by
  simp [eplus, scOne, iota]

/-- Ненулевая связь после потери проекции **не** восстанавливает удалённый
    сектор: если выходы совпали до наблюдения, они совпадут и после. -/
theorem lossy_cannot_recover (lam : ℚ) (u : SC)
    (h : mulSC u scOne = mulSC u iota) :
    Pi lam (mulSC u scOne) = Pi lam (mulSC u iota) := by
  rw [h]

/-! ## 3. `Π_λ` не мультипликативна

Мультипликативность потребовала бы `Π_λ(e₊e₋) = Π_λ(e₊)·Π_λ(e₋)`, но слева
`0`, а справа `λ(1−λ) > 0` при `0 < λ < 1`. Значит автоматического функтора
«фаза → вероятность» нет. -/

theorem Pi_not_multiplicative (lam : ℚ) (h0 : 0 < lam) (h1 : lam < 1) :
    Pi lam (mulSC eplus eminus) ≠ Pi lam eplus * Pi lam eminus := by
  simp only [Pi, mulSC, eplus, eminus, mul_zero, mul_one, add_zero, zero_add]
  intro h
  nlinarith

/-- Численная иллюстрация: при `λ = 1/2` слева `0`, справа `1/4`. -/
theorem Pi_half_witness :
    Pi (1 / 2) (mulSC eplus eminus) = 0 ∧ Pi (1 / 2) eplus * Pi (1 / 2) eminus = 1 / 4 := by
  constructor <;> norm_num [Pi, mulSC, eplus, eminus]

/-! ## 3b. ТОЧНЫЙ ДЕФЕКТ ПРОЕКЦИИ (ADDENDUM-002, H1)

Выше немультипликативность доказана одной точкой (`e₊e₋`). Здесь она
измеряется полностью: дефект — **полиномиальное тождество** с множителем
`λ(1−λ)` и «знаковым рассогласованием» `(z₊−z₋)(w₊−w₋)`.

Замечание о базисе: тождество верно именно при **покомпонентном** умножении
в базисе `e₊, e₋` (это и есть умножение `Q₋₁`). В базисе `1, ι` та же
формула имела бы другой вид, поэтому здесь зафиксирован `mulSC`. -/

/-- **Точный дефект проекции (H1).** Для всех `λ`, `z`, `w`:
`Π_λ(z·w) − Π_λ(z)·Π_λ(w) = λ(1−λ)(z₊−z₋)(w₊−w₋)`.
Гипотез нет — это тождество многочленов. -/
theorem Pi_defect (lam : ℚ) (z w : SC) :
    Pi lam (mulSC z w) - Pi lam z * Pi lam w =
      lam * (1 - lam) * ((z.1 - z.2) * (w.1 - w.2)) := by
  simp only [Pi, mulSC_fst, mulSC_snd]
  ring

/-- **Мультипликативность на всей `R = ℚ×ℚ` ⇔ вырождение проекции.**
`Π_λ` мультипликативна для всех `z, w` тогда и только тогда, когда `λ = 0`
или `λ = 1`. Промежуточных значений нет: любой `0 < λ < 1` даёт дефект. -/
theorem Pi_multiplicative_iff (lam : ℚ) :
    (∀ z w : SC, Pi lam (mulSC z w) = Pi lam z * Pi lam w) ↔ lam = 0 ∨ lam = 1 := by
  constructor
  · intro h
    have hd := Pi_defect lam eplus eminus
    rw [h eplus eminus] at hd
    have hprod : (eplus.1 - eplus.2) * (eminus.1 - eminus.2) = -1 := by
      simp [eplus, eminus]
    have hzero : lam * (1 - lam) = 0 := by
      rw [hprod] at hd
      linarith
    rcases mul_eq_zero.mp hzero with h0 | h1
    · exact Or.inl h0
    · exact Or.inr (by linarith)
  · rintro (rfl | rfl) z w <;> simp [Pi]

/-- **Контроль H1:** `e₊·e₋ = 0`, поэтому дефект равен `−λ(1−λ)`.
Знак минус важен: дефект не «просто мал», он отрицателен на этой паре. -/
theorem Pi_defect_eplus_eminus (lam : ℚ) :
    Pi lam (mulSC eplus eminus) - Pi lam eplus * Pi lam eminus = -(lam * (1 - lam)) := by
  rw [Pi_defect]
  have h : (eplus.1 - eplus.2) * (eminus.1 - eminus.2) = -1 := by
    simp [eplus, eminus]
  rw [h]
  ring

/-- **Инъективность умножения на фазу.** Умножение на `u` в `R = ℚ×ℚ`
инъективно тогда и только тогда, когда **обе** компоненты `u` ненулевые.
Одного `u₋ ≠ 0` недостаточно — замечание координатора в ADDENDUM-002 (H3)
принято и зафиксировано здесь как теорема, а не как оговорка. -/
theorem mulSC_injective_iff (u : SC) :
    Function.Injective (mulSC u) ↔ u.1 ≠ 0 ∧ u.2 ≠ 0 := by
  constructor
  · intro h
    constructor
    · intro h1
      have heq : mulSC u (0, 0) = mulSC u (1, 0) := by simp [mulSC, h1]
      have hc : (0 : ℚ) = 1 := by
        have := congrArg Prod.fst (h heq)
        simpa using this
      exact zero_ne_one hc
    · intro h2
      have heq : mulSC u (0, 0) = mulSC u (0, 1) := by simp [mulSC, h2]
      have hc : (0 : ℚ) = 1 := by
        have := congrArg Prod.snd (h heq)
        simpa using this
      exact zero_ne_one hc
  · rintro ⟨h1, h2⟩ z w hzw
    have hfst : u.1 * z.1 = u.1 * w.1 := by
      simpa [mulSC] using congrArg Prod.fst hzw
    have hsnd : u.2 * z.2 = u.2 * w.2 := by
      simpa [mulSC] using congrArg Prod.snd hzw
    exact Prod.ext (mul_left_cancel₀ h1 hfst) (mul_left_cancel₀ h2 hsnd)

/-! ## 4. Выпуклые смеси сохраняют стохастичность

Это единственное, что проекция обязана сохранять: если два канала по
отдельности стохастические, их выпуклая смесь тоже. -/

theorem convex_mix_nonneg {α : Type*} (p q : α → ℚ) (lam : ℚ)
    (hp : ∀ i, 0 ≤ p i) (hq : ∀ i, 0 ≤ q i) (h0 : 0 ≤ lam) (h1 : lam ≤ 1) (i : α) :
    0 ≤ lam * p i + (1 - lam) * q i := by
  have h1' : 0 ≤ 1 - lam := by linarith
  exact add_nonneg (mul_nonneg h0 (hp i)) (mul_nonneg h1' (hq i))

theorem convex_mix_sum {α : Type*} [Fintype α] (p q : α → ℚ) (lam : ℚ)
    (hp : ∑ i, p i = 1) (hq : ∑ i, q i = 1) :
    ∑ i, (lam * p i + (1 - lam) * q i) = 1 := by
  rw [Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.mul_sum, hp, hq]
  ring

/-- Смесь двух стохастических каналов — стохастический канал. -/
theorem convex_mix_stochastic {α : Type*} [Fintype α] (p q : α → ℚ) (lam : ℚ)
    (hp : ∀ i, 0 ≤ p i) (hq : ∀ i, 0 ≤ q i)
    (hsp : ∑ i, p i = 1) (hsq : ∑ i, q i = 1)
    (h0 : 0 ≤ lam) (h1 : lam ≤ 1) :
    (∀ i, 0 ≤ lam * p i + (1 - lam) * q i) ∧
      ∑ i, (lam * p i + (1 - lam) * q i) = 1 :=
  ⟨convex_mix_nonneg p q lam hp hq h0 h1, convex_mix_sum p q lam hsp hsq⟩

end Bridge
end QCat
