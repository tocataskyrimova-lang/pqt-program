import Std

/-!
# Сравнение двух моделей брейдинга и их классов переписываний (этап 4bis + QLP-03)

В проекте сосуществуют две **разные** реализации, и это надо фиксировать явно:

| | исторический QCat (`QMath_v3.md`, `Historical.lean`) | диэдральная R (`RMap.lean`, `StdOnly.lean`) |
|---|---|---|
| действие | `σ(a,b) = ω(a,b)·(b,a)` | `R(a,b) = (b, 2b−a) mod 64` |
| метки кодонов | сохраняются, меняется только порядок | меняются (аффинная трансвекция) |
| фаза | скаляр из `Q₋₁ˣ` | отсутствует |
| порядок на метках | 2 (`σ²` возвращает `(a,b)` при любой ω) | 64 (`R⁶⁴=id`, `R²≠id`) |
| группа | перестановки позиций + характер | циклическая `Z/64` |
| естественные переписывания | при `ω≡1` — **любые** `f` | не все: сдвиг `f(a)=a+1` не естественен |

**Зачем это.** `R`-модель удобна для ограничений естественности, но она не
является брейдинговым генератором первичного QCat. Выводы о допустимых
переписываниях из `R` нельзя автоматически переносить на `σᵢ`, и наоборот.
Вывод `Naturality.lean` о существенности гипотезы `F(r) ≠ 0` относится к
скалярно-фазовой модели и остаётся `not_claimed` для полной теоремы N1.

**QLP-03 (аудит Илори).** Прежняя теорема `rewrite_classes_differ` доказывала
только различие **действий на метках**, а не различие классов естественных
переписываний. Исправлено:

* теорема переименована в `braid_label_actions_differ` — это ровно то, что
  она доказывает;
* добавлен предикат `NaturalRewrite` (односторонняя естественность
  `β ∘ (f ⊗ I) = (I ⊗ f) ∘ β`);
* доказано `natural_rewrite_classes_differ`: для `flip` (ω≡1) естественна
  **любая** `f : C → C`, а для `R` сдвиг `f(a)=a+1` — нет
  (`(0,63) ≠ (0,1)` при `a=b=0`).

**Что доказано здесь (только ядро Lean + `Std`).**
1. Никакая фазовая таблица `ω` не делает `σ` равной `R`: уже на паре `(0,1)`
   меточная часть `σ` равна `(1,0)`, а `R` равна `(1,2)`.
2. `σ` на метках — инволюция для **любой** `ω`; `R` на метках имеет порядок 64.
3. `R` выводит за пределы исходной пары меток (`2 ∉ {0,1}`), `σ` — никогда.
4. `braid_label_actions_differ` — различие действий на метках.
5. `natural_rewrite_classes_differ` — различие классов естественных
   переписываний (QLP-03).

Фазовый тип здесь `Bool` — конечная абстракция. Результат (1) от кольца фаз
**не зависит**: меточная часть `σ` вообще не использует `ω`.
-/

namespace QCat.Comparison

/-- 64 кодона как `Fin 64` (совпадает с `Σ³` по мощности). -/
abbrev Codon := Fin 64

/-- Конечная абстракция `Q₋₁ˣ`. -/
abbrev Phase := Bool

/-- Историческая σ: перестановка позиций + скалярная фаза. -/
def sigma (omega : Codon → Codon → Phase) (p : Codon × Codon) :
    Phase × (Codon × Codon) :=
  (omega p.1 p.2, (p.2, p.1))

/-- Диэдральная R (трансвекция `I + N`, `N² = 0`). -/
def R (a b : Codon) : Codon × Codon := (b, 2 * b - a)

def Rpow : Nat → Codon × Codon → Codon × Codon
  | 0, p => p
  | k + 1, p => Rpow k (R p.1 p.2)

/-- **QLP-03:** односторонняя естественность rewrite-генератора `f`
    относительно брейдинга `β`:
    `β ∘ (f ⊗ I) = (I ⊗ f) ∘ β`, то есть
    `β (f a, b) = (β(a,b).1, f (β(a,b).2))`. -/
def NaturalRewrite (β : Codon × Codon → Codon × Codon) (f : Codon → Codon) : Prop :=
  ∀ a b : Codon, β (f a, b) = ((β (a, b)).1, f ((β (a, b)).2))

/-- Обычный flip: `ω ≡ 1`. -/
def flip : Codon × Codon → Codon × Codon := fun p => (p.2, p.1)

/-- Сдвиг метки на 1 — кандидат в rewrite-генераторы. -/
def shift1 (a : Codon) : Codon := a + 1

/-- σ на метках — инволюция при любой фазовой таблице. -/
theorem sigma_label_involutive (omega : Codon → Codon → Phase)
    (p : Codon × Codon) :
    (sigma omega ((sigma omega p).2)).2 = p := by
  rfl

/-- **Никакая ω не реализует R.** Сравниваем меточные части. -/
theorem no_phase_table_realizes_R (omega : Codon → Codon → Phase) :
    (sigma omega (0, 1)).2 ≠ R (0 : Codon) 1 := by
  -- меточная часть σ не зависит от ω, поэтому цель замкнута
  change ((1 : Codon), (0 : Codon)) ≠ R (0 : Codon) 1
  native_decide

/-- R меняет содержимое кодона: значение `2` отсутствует в исходной паре. -/
theorem R_changes_codon_labels :
    (R 0 1).2 ≠ (0 : Codon) ∧ (R 0 1).2 ≠ (1 : Codon) := by
  native_decide

/-- σ никогда не меняет мультимножество меток пары. -/
theorem sigma_preserves_label_pair (omega : Codon → Codon → Phase)
    (a b : Codon) :
    (sigma omega (a, b)).2 = (b, a) := by
  rfl

/-- Порядок R на орбите `(0,1)` равен 64 (согласовано со `StdOnly.lean`). -/
theorem R_order_on_orbit :
    Rpow 64 (0, 1) = (0, 1) ∧
      Rpow 32 (0, 1) ≠ (0, 1) ∧
        Rpow 2 (0, 1) ≠ (0, 1) := by
  native_decide

/-- **QLP-03:** при `ω ≡ 1` (обычный flip) естественна любая перестановка
    меток: `flip ∘ (f ⊗ I) = (I ⊗ f) ∘ flip` выполняется тождественно. -/
theorem flip_every_rewrite_natural (f : Codon → Codon) :
    NaturalRewrite flip f := by
  intro a b
  rfl

/-- **QLP-03:** для диэдральной `R` сдвиг `f(a)=a+1` НЕ естественен.
    При `a=b=0` левая часть даёт `(0,63)`, правая — `(0,1)`. -/
theorem R_shift1_not_natural :
    ¬ NaturalRewrite (fun p : Codon × Codon => R p.1 p.2) shift1 := by
  intro h
  have h00 := h 0 0
  have hne : R (shift1 0) 0 ≠ ((R 0 0).1, shift1 ((R 0 0).2)) := by
    native_decide
  exact hne h00

/-- **QLP-03, главное:** классы естественных переписываний различны.
    Для flip естественно всё, для R — не всё. -/
theorem natural_rewrite_classes_differ :
    (∀ f : Codon → Codon, NaturalRewrite flip f) ∧
      ¬ NaturalRewrite (fun p : Codon × Codon => R p.1 p.2) shift1 :=
  ⟨flip_every_rewrite_natural, R_shift1_not_natural⟩

/-- **Переименовано по QLP-03.** Теорема доказывает различие *действий на
    метках*, а не различие классов естественных переписываний
    (для последнего см. `natural_rewrite_classes_differ`).
    У σ меточная динамика порядка 2, у R — порядка 64. -/
theorem braid_label_actions_differ :
    (∀ (omega : Codon → Codon → Phase) (p : Codon × Codon),
      (sigma omega ((sigma omega p).2)).2 = p) ∧
    (∃ p : Codon × Codon, Rpow 2 p ≠ p ∧ Rpow 64 p = p) := by
  constructor
  · intro omega p
    rfl
  · refine ⟨(0, 1), ?_, ?_⟩ <;> native_decide

#print axioms sigma_label_involutive
#print axioms no_phase_table_realizes_R
#print axioms R_changes_codon_labels
#print axioms R_order_on_orbit
#print axioms braid_label_actions_differ
#print axioms flip_every_rewrite_natural
#print axioms R_shift1_not_natural
#print axioms natural_rewrite_classes_differ

end QCat.Comparison
