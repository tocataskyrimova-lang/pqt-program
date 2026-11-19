import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

/-!
# Арифметическая модель R на `ZMod 64`

Проверяемая часть стартового фрагмента Илори (2026-11-07), доведённая от
двух `decide`-примеров до универсальных утверждений с кванторами.

**Граница модели (важно для сверки с QCat).** Это НЕ генератор `σᵢ` из
`QMath_v3.md` §2: там braiding — фазированный swap позиций
`(x, y) ↦ ω(x,y) · (y, x)` с `ω : Σ×Σ → Q₋₁ˣ`. Здесь
`R(a,b) = (b, 2b − a)` — унипотентная транспекция `I + N`, `N² = 0`,
на двумерном модуле над `ZMod 64`. YBE для неё выполняется, но это
утверждение об R, а не о QCat-брайдинге.
-/

namespace QCat.RMap

abbrev Z := ZMod 64

/-- Стартовое определение Илори, без изменений. -/
def R (a b : Z) : Z × Z := (b, 2 * b - a)

/-- Явное обратное: `R = I + N`, `N² = 0` ⇒ `R⁻¹ = I − N`. -/
def Rinv (a b : Z) : Z × Z := (2 * a - b, a)

/-- Действие R на первую пару координат тройки (`σ₁`). -/
def R12 (t : Z × Z × Z) : Z × Z × Z :=
  ((R t.1 t.2.1).1, (R t.1 t.2.1).2, t.2.2)

/-- Действие R на вторую пару координат тройки (`σ₂`). -/
def R23 (t : Z × Z × Z) : Z × Z × Z :=
  (t.1, (R t.2.1 t.2.2).1, (R t.2.1 t.2.2).2)

/-- k-кратное применение R. -/
def Rpow : Nat → Z × Z → Z × Z
  | 0, p => p
  | k + 1, p => Rpow k (R p.1 p.2)

section StarterFragment

/-- Пример 1 из фрагмента Илори: проверен. -/
example : R 0 1 = (1, 2) := by decide

/-- Пример 2 из фрагмента Илори: проверен (контрпример к инволютивности). -/
example : R (R 0 1).1 (R 0 1).2 ≠ (0, 1) := by decide

end StarterFragment

section Invertibility

/-- `R ∘ R⁻¹ = id` (универсально, не на конкретной точке). -/
theorem R_Rinv (a b : Z) : R (Rinv a b).1 (Rinv a b).2 = (a, b) := by
  ext <;> simp [R, Rinv]

/-- `R⁻¹ ∘ R = id`. -/
theorem Rinv_R (a b : Z) : Rinv (R a b).1 (R a b).2 = (a, b) := by
  ext <;> simp [R, Rinv]

end Invertibility

section YangBaxter

/-- (B2) Yang–Baxter: `R12 R23 R12 = R23 R12 R23`, для всех троек. -/
theorem yang_baxter (t : Z × Z × Z) :
    R12 (R23 (R12 t)) = R23 (R12 (R23 t)) := by
  rcases t with ⟨a, b, c⟩
  ext <;> simp [R12, R23, R] <;> ring

/-- (B1) локальная коммутативность для непересекающихся позиций
    (на четвёрке координат R действует на 1–2 и 3–4 независимо). -/
def R34 (t : Z × Z × Z × Z) : Z × Z × Z × Z :=
  (t.1, t.2.1, (R t.2.2.1 t.2.2.2).1, (R t.2.2.1 t.2.2.2).2)

def R12₄ (t : Z × Z × Z × Z) : Z × Z × Z × Z :=
  ((R t.1 t.2.1).1, (R t.1 t.2.1).2, t.2.2.1, t.2.2.2)

theorem local_commutativity (t : Z × Z × Z × Z) :
    R12₄ (R34 t) = R34 (R12₄ t) := by
  rcases t with ⟨a, b, c, d⟩
  ext <;> simp [R12₄, R34, R]

end YangBaxter

section Order

/-- Ключевая формула: `Rᵏ(a,b) = (a + k(b−a), b + k(b−a))`.
    Индукция по k, а не перебор конечного типа. -/
theorem Rpow_formula (k : Nat) (a b : Z) :
    Rpow k (a, b) = (a + (k : Z) * (b - a), b + (k : Z) * (b - a)) := by
  induction k generalizing a b with
  | zero => simp [Rpow]
  | succ k ih =>
      -- Раскрываем и рекурсию, и саму R: иначе в целях остаются `(R a b).1`.
      simp only [Rpow, R]
      rw [ih b (2 * b - a)]
      ext <;> push_cast <;> ring_nf

/-- `R⁶⁴ = id`: `(64 : ZMod 64) = 0` — лемма `ZMod.natCast_self 64`,
    `norm_num` её сам не находит. -/
theorem Rpow_64 (a b : Z) : Rpow 64 (a, b) = (a, b) := by
  rw [Rpow_formula]
  -- `↑64` здесь — Nat.cast, а не OfNat-число; `ZMod.natCast_self` имеет
  -- ровно такой тип: `((64 : ℕ) : ZMod 64) = 0`.
  rw [ZMod.natCast_self 64]
  simp

/-- `R² ≠ id` как универсальное опровержение, а не один пример. -/
theorem not_involutive : ¬ (∀ p : Z × Z, Rpow 2 p = p) := by
  intro h
  have hp : Rpow 2 ((0 : Z), (1 : Z)) = ((0 : Z), (1 : Z)) := h ((0 : Z), (1 : Z))
  have hne : Rpow 2 ((0 : Z), (1 : Z)) ≠ ((0 : Z), (1 : Z)) := by decide
  exact hne hp

/-- Порядок R ровно 64 на орбите точки (0,1): 32 шага ещё не возвращают. -/
theorem Rpow_32_ne :
    Rpow 32 ((0 : Z), (1 : Z)) ≠ ((0 : Z), (1 : Z)) := by
  decide

/-- `R³² ≠ (0,1)` и `R⁶⁴ = (0,1)` вместе дают порядок 64 на этой орбите. -/
example : Rpow 64 ((0 : Z), (1 : Z)) = ((0 : Z), (1 : Z)) :=
  Rpow_64 (0 : Z) (1 : Z)

end Order

end QCat.RMap
