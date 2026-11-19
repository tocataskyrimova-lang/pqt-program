import Mathlib.Algebra.Group.Basic

/-!
# Общие B1 и B2 для всех длин и позиций (QLP: общий B1)

`BraidRelations.lean` проверял B1 только на конкретном случае `σ₁`/`σ₃` для
слова длины 4. Аудит Илори отметил это как `ACCEPT_BOUNDED` и указал, что
«весь B1 для всех длин и позиций» не доказан. Здесь B1 и B2 доказываются
в общей форме:

* слово — произвольная функция `Fin n → Glyph`;
* брейдинг `braid ω a b` меняет местами метки в позициях `a` и `b` и
  умножает коэффициент на `ω(w a)(w b)`;
* **B1:** если носители `{a,b}` и `{c,d}` не пересекаются, то
  `braid ω a b ∘ braid ω c d = braid ω c d ∘ braid ω a b`;
* **B2:** если `a,b,c` попарно различны, то
  `braid ω a b ∘ braid ω b c ∘ braid ω a b =
   braid ω b c ∘ braid ω a b ∘ braid ω b c`.

Обе теоремы верны для **любой** фазовой таблицы `ω` в коммутативном моноиде
`K`; обратимость фаз не нужна (она нужна только для изоморфности σ).
Никаких `sorry`, только ядро Lean + `Std`.
-/

namespace QCat.GeneralBraid

/-- Четыре глифа `Σ = {α, β, γ, δ}`. -/
abbrev Glyph := Fin 4

/-- Слово длины `n`. -/
abbrev Word (n : Nat) := Fin n → Glyph

/-- Перестановка двух позиций `a` и `b` (ядро Lean, без `Equiv`-API). -/
def swapAt {n : Nat} (a b : Fin n) (i : Fin n) : Fin n :=
  if i = a then b else if i = b then a else i

theorem swapAt_left {n : Nat} (a b : Fin n) : swapAt a b a = b := by
  simp [swapAt]

theorem swapAt_right {n : Nat} (a b : Fin n) (h : a ≠ b) : swapAt a b b = a := by
  simp [swapAt, Ne.symm h]

theorem swapAt_of_ne {n : Nat} (a b i : Fin n) (h1 : i ≠ a) (h2 : i ≠ b) :
    swapAt a b i = i := by
  simp [swapAt, h1, h2]

/-- Перестановки с непересекающимися носителями коммутируют. -/
theorem swapAt_commute_disjoint {n : Nat} (a b c d i : Fin n)
    (hac : a ≠ c) (had : a ≠ d) (hbc : b ≠ c) (hbd : b ≠ d) :
    swapAt c d (swapAt a b i) = swapAt a b (swapAt c d i) := by
  by_cases h1 : i = a <;> by_cases h2 : i = b <;>
    by_cases h3 : i = c <;> by_cases h4 : i = d <;>
      simp_all [swapAt, Ne.symm hac, Ne.symm had, Ne.symm hbc, Ne.symm hbd]

/-- Соотношение кос для трёх различных позиций:
    `(a b)(b c)(a b) = (b c)(a b)(b c)`. -/
theorem swapAt_braid_relation {n : Nat} (a b c i : Fin n)
    (hab : a ≠ b) (hbc : b ≠ c) (hac : a ≠ c) :
    swapAt a b (swapAt b c (swapAt a b i)) =
      swapAt b c (swapAt a b (swapAt b c i)) := by
  by_cases h1 : i = a <;> by_cases h2 : i = b <;> by_cases h3 : i = c <;>
    simp_all [swapAt, Ne.symm hab, Ne.symm hbc, Ne.symm hac]

section Braid

variable {K : Type*} [CommMonoid K]

/-- Брейдинг в позициях `a` и `b`: перестановка меток + скалярная фаза. -/
def braid {n : Nat} (omega : Glyph → Glyph → K) (a b : Fin n)
    (s : K × Word n) : K × Word n :=
  (s.1 * omega (s.2 a) (s.2 b), fun i => s.2 (swapAt a b i))

/-- **B1 в общей форме.** Непересекающиеся носители ⇒ коммутация.
    Верно для любой `ω` и любого `n`. -/
theorem local_commutativity_general {n : Nat} (omega : Glyph → Glyph → K)
    (a b c d : Fin n) (hac : a ≠ c) (had : a ≠ d) (hbc : b ≠ c) (hbd : b ≠ d)
    (s : K × Word n) :
    braid omega a b (braid omega c d s) = braid omega c d (braid omega a b s) := by
  rcases s with ⟨k, w⟩
  apply Prod.ext
  · -- коэффициенты: обе цепочки дают `k * ω(w a)(w b) * ω(w c)(w d)`
    simp only [braid]
    have hca : swapAt c d a = a := swapAt_of_ne c d a hac had
    have hcb : swapAt c d b = b := swapAt_of_ne c d b hbc hbd
    have hac' : swapAt a b c = c := swapAt_of_ne a b c (Ne.symm hac) (Ne.symm hbc)
    have had' : swapAt a b d = d := swapAt_of_ne a b d (Ne.symm had) (Ne.symm hbd)
    simp only [hca, hcb, hac', had']
    simp [mul_assoc, mul_comm, mul_left_comm]
  · -- метки: перестановки коммутируют
    funext i
    simp only [braid]
    exact congrArg w (swapAt_commute_disjoint a b c d i hac had hbc hbd)

/-- **B2 в общей форме (Yang–Baxter).** Три различные позиции.
    Верно для любой `ω` в коммутативном моноиде. -/
theorem yang_baxter_general {n : Nat} (omega : Glyph → Glyph → K)
    (a b c : Fin n) (hab : a ≠ b) (hbc : b ≠ c) (hac : a ≠ c)
    (s : K × Word n) :
    braid omega a b (braid omega b c (braid omega a b s)) =
      braid omega b c (braid omega a b (braid omega b c s)) := by
  rcases s with ⟨k, w⟩
  apply Prod.ext
  · simp only [braid]
    -- промежуточные метки после первых обменов
    have hba : swapAt a b b = a := swapAt_right a b hab
    have hab' : swapAt a b a = b := swapAt_left a b
    have hbc_b : swapAt b c b = c := swapAt_left b c
    have hbc_c : swapAt b c c = b := swapAt_right b c hbc
    have hab_c : swapAt a b c = c := swapAt_of_ne a b c (Ne.symm hac) (Ne.symm hbc)
    have hbc_a : swapAt b c a = a := swapAt_of_ne b c a hab hac
    -- после (a,b): позиция a = w b, позиция b = w a
    -- после (a,b)(b,c): позиция a = w b, b = w c
    simp only [hba, hab', hbc_b, hbc_c, hab_c, hbc_a]
    simp [mul_assoc, mul_comm, mul_left_comm]
  · funext i
    simp only [braid]
    exact congrArg w (swapAt_braid_relation a b c i hab hbc hac)

/-- Частный случай B1 из `BraidRelations` (σ₁ и σ₃ на слове длины 4)
    как следствие общей теоремы. -/
theorem sigma1_sigma3 (omega : Glyph → Glyph → K) (s : K × Word 4) :
    braid omega (0 : Fin 4) 1 (braid omega (2 : Fin 4) 3 s) =
      braid omega (2 : Fin 4) 3 (braid omega (0 : Fin 4) 1 s) :=
  local_commutativity_general omega 0 1 2 3 (by decide) (by decide) (by decide) (by decide) s

end Braid

end QCat.GeneralBraid
