import Std

/-!
# Независимый слой: R на `Fin 64` без Mathlib

Сборочно независимая проверка того же фрагмента Илори. Здесь `ZMod 64`
заменён на `Fin 64` с его встроенной модульной арифметикой (это то же
кольцо вычетов), а все утверждения доказываются исчерпывающим перебором
конечного типа, а не символьной алгеброй.

Зачем два слоя: символьные доказательства в `RMap.lean` опираются на
`ring`/Mathlib, этот файл — только на ядро Lean и `Std`. Совпадение
результатов даёт независимую проверку YBE и формулы степеней.

Аудит: `native_decide` использует kernel-примитив `Lean.ofReduceBool`
(доверие скомпилированному коду), пользовательских аксиом и `sorry` нет.
-/

namespace QCat.StdOnly

abbrev Z := Fin 64

def R (a b : Z) : Z × Z := (b, 2 * b - a)
def Rinv (a b : Z) : Z × Z := (2 * a - b, a)

def R12 (t : Z × Z × Z) : Z × Z × Z :=
  ((R t.1 t.2.1).1, (R t.1 t.2.1).2, t.2.2)
def R23 (t : Z × Z × Z) : Z × Z × Z :=
  (t.1, (R t.2.1 t.2.2).1, (R t.2.1 t.2.2).2)

def Rpow : Nat → Z × Z → Z × Z
  | 0, p => p
  | k + 1, p => Rpow k (R p.1 p.2)

/-- Примеры Илори: проверены ядром. -/
example : R 0 1 = (1, 2) := by decide
example : R (R 0 1).1 (R 0 1).2 ≠ (0, 1) := by decide

/-- Обратимость: обе композиции, для всех 4096 пар. -/
theorem R_Rinv : ∀ a b : Z, R (Rinv a b).1 (Rinv a b).2 = (a, b) := by
  native_decide

theorem Rinv_R : ∀ a b : Z, Rinv (R a b).1 (R a b).2 = (a, b) := by
  native_decide

/-- Yang–Baxter: полный перебор 64³ = 262144 троек. -/
theorem yang_baxter : ∀ a b c : Z,
    R12 (R23 (R12 (a, b, c))) = R23 (R12 (R23 (a, b, c))) := by
  native_decide

/-- Формула k-й степени: перебор k = 0…70 и всех 4096 пар. -/
theorem Rpow_formula : ∀ k : Fin 71, ∀ a b : Z,
    Rpow k.val (a, b) =
      (a + (Fin.ofNat' 64 k.val) * (b - a),
       b + (Fin.ofNat' 64 k.val) * (b - a)) := by
  native_decide

/-- `R⁶⁴ = id` для всех пар. -/
theorem Rpow_64 : ∀ a b : Z, Rpow 64 (a, b) = (a, b) := by
  native_decide

/-- `R² ≠ id`: существует точка, где квадрат не тождество. -/
theorem not_involutive : ∃ p : Z × Z, Rpow 2 p ≠ p := by
  refine ⟨(0, 1), ?_⟩
  decide

/-- Порядок на орбите (0,1) ровно 64: 32 шага ещё не возвращают. -/
theorem order_witness : Rpow 32 (0, 1) ≠ (0, 1) ∧ Rpow 64 (0, 1) = (0, 1) := by
  decide

#print axioms R_Rinv
#print axioms yang_baxter
#print axioms Rpow_formula
#print axioms Rpow_64
#print axioms not_involutive
#print axioms order_witness

end QCat.StdOnly
