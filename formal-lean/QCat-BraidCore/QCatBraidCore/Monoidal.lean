import QCatBraidCore.Basic
import Mathlib.CategoryTheory.Monoidal.Category

/-!
# Моноидальная структура на `BraidCore` (QCAT-CATEGORY-CLOSURE-007, п.3)

Тензор — дизъюнктное объединение носителей (в QCat это сложение числа
кодонов: `m ⊗ n = m + n`), единица — пустой носитель (`I = 0`).
Ассоциатор и юниторы — стандартные биекции `Equiv.sumAssoc`,
`Equiv.emptySum`, `Equiv.sumEmpty`; все они имеют единичную фазу.

**Конструктивность.** Пентагон, треугольник и естественность доказываются
поточечно: после `ext` и разбора вариантов суммы обе части сводятся к одной
и той же функции, поэтому цель закрывается `rfl`. Никаких `axiom`/`sorry`.

**Почему не `simp`.** `(X ⊗ Y).carrier` и `(𝟙_ _).carrier` — это проекции
структуры `BraidCore`, накрытые проекцией поля экземпляра `MonoidalCategory`.
Они *дефиниционно* равны `X.carrier ⊕ Y.carrier` и `PEmpty`, но `simp`
не разворачивает цепочку проекций и не находит `IsEmpty` для `𝟙_`.
Поэтому в «носительных» целях используется `rfl`/`PEmpty.elim`, а не `simp`.
-/

open CategoryTheory
open CategoryTheory.MonoidalCategory

namespace QCat
namespace BraidCore

variable {K : Type} [CommMonoid K]

/-- Тензор объектов: `X ⊗ Y` — носитель `X.carrier ⊕ Y.carrier`. -/
def tensorObj (X Y : BraidCore K) : BraidCore K := ⟨X.carrier ⊕ Y.carrier⟩

/-- Единица тензора: пустой носитель (0 кодонов). -/
def tensorUnit : BraidCore K := ⟨PEmpty⟩

/-- **Моноидальная структура.** Все компоненты — явные функции;
    когерентность доказывается, а не постулируется. -/
instance instMonoidalCategory : MonoidalCategory (BraidCore K) where
  tensorObj := tensorObj
  tensorUnit := tensorUnit
  whiskerLeft X {Y₁ Y₂} f := ⟨f.phase, Equiv.sumCongr (Equiv.refl X.carrier) f.perm⟩
  whiskerRight {X₁ X₂} f Y := ⟨f.phase, Equiv.sumCongr f.perm (Equiv.refl Y.carrier)⟩
  associator X Y Z := isoOfEquiv (Equiv.sumAssoc X.carrier Y.carrier Z.carrier)
  leftUnitor X := isoOfEquiv (Equiv.emptySum PEmpty X.carrier)
  rightUnitor X := isoOfEquiv (Equiv.sumEmpty X.carrier PEmpty)
  tensorHom_def f g := rfl
  tensor_id X₁ X₂ := by
    apply Hom.ext
    · simp
    · ext x
      rcases x with (a | b) <;> rfl
  tensor_comp f₁ f₂ g₁ g₂ := by
    apply Hom.ext
    · simp [mul_assoc, mul_comm, mul_left_comm]
    · ext x
      rcases x with (a | b) <;> rfl
  whiskerLeft_id X Y := by
    apply Hom.ext
    · simp
    · ext x
      rcases x with (a | b) <;> rfl
  id_whiskerRight X Y := by
    apply Hom.ext
    · simp
    · ext x
      rcases x with (a | b) <;> rfl
  associator_naturality f₁ f₂ f₃ := by
    apply Hom.ext
    · simp [mul_assoc]
    · ext x
      rcases x with ((a | b) | c) <;> rfl
  leftUnitor_naturality f := by
    apply Hom.ext
    · simp
    · ext x
      rcases x with (e | a)
      · exact PEmpty.elim e
      · rfl
  rightUnitor_naturality f := by
    apply Hom.ext
    · simp
    · ext x
      rcases x with (a | e)
      · rfl
      · exact PEmpty.elim e
  pentagon W X Y Z := by
    apply Hom.ext
    · simp
    · ext x
      rcases x with (((a | b) | c) | d) <;> rfl
  triangle X Y := by
    apply Hom.ext
    · simp
    · ext x
      rcases x with ((a | e) | b)
      · rfl
      · exact PEmpty.elim e
      · rfl

/-! ### Разворачивающие леммы для носителей

Эти леммы нужны ниже (браiding) и в downstream-файлах: они позволяют
переписать `(X ⊗ Y).carrier` и `(𝟙_ _).carrier` там, где `rfl` уже
не срабатывает (например, внутри `simp`-наборов). -/

@[simp]
theorem tensorObj_carrier (X Y : BraidCore K) :
    (X ⊗ Y).carrier = (X.carrier ⊕ Y.carrier) := rfl

@[simp]
theorem tensorUnit_carrier : (𝟙_ (BraidCore K)).carrier = PEmpty := rfl

/-- Экземпляр `IsEmpty` для носителя единицы — в форме, пригодной для
    `instance`-поиска (проекция `𝟙_` сама по себе его не даёт). -/
instance instIsEmptyTensorUnitCarrier : IsEmpty (𝟙_ (BraidCore K)).carrier := by
  rw [tensorUnit_carrier]
  infer_instance

/-! ### Фазовые проекции структурных морфизмов

Все структурные изоморфизмы (ассоциатор, юниторы) имеют фазу `1`,
а «обводки» (`◁`, `▷`) не меняют фазу. Эти леммы — `rfl`: они не
доказывают ничего нового, но дают `simp` точку входа, которой ему
не хватает из-за цепочки проекций структуры. -/

@[simp]
theorem whiskerLeft_phase {X Y Z : BraidCore K} (f : Y ⟶ Z) :
    (X ◁ f).phase = f.phase := rfl

@[simp]
theorem whiskerRight_phase {X Y Z : BraidCore K} (f : X ⟶ Y) :
    (f ▷ Z).phase = f.phase := rfl

@[simp]
theorem associator_hom_phase (X Y Z : BraidCore K) : (α_ X Y Z).hom.phase = 1 := rfl

@[simp]
theorem associator_inv_phase (X Y Z : BraidCore K) : (α_ X Y Z).inv.phase = 1 := rfl

@[simp]
theorem leftUnitor_hom_phase (X : BraidCore K) : (λ_ X).hom.phase = 1 := rfl

@[simp]
theorem leftUnitor_inv_phase (X : BraidCore K) : (λ_ X).inv.phase = 1 := rfl

@[simp]
theorem rightUnitor_hom_phase (X : BraidCore K) : (ρ_ X).hom.phase = 1 := rfl

@[simp]
theorem rightUnitor_inv_phase (X : BraidCore K) : (ρ_ X).inv.phase = 1 := rfl

end BraidCore
end QCat
