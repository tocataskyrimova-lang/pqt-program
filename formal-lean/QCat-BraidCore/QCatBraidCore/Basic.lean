import Mathlib.Algebra.Group.Basic
import Mathlib.Algebra.Group.Units.Defs
import Mathlib.CategoryTheory.Category.Basic
import Mathlib.CategoryTheory.Iso
import Mathlib.Logic.Equiv.Sum

/-!
# BraidCore: категория «фаза + биекция» (QCAT-CATEGORY-CLOSURE-007, п.3)

Это **конструктивная** модель структурного скелета исторического QCat:
объект — носитель меток (в QCat это набор кодонов; `𝟙_` — пустой носитель,
то есть 0 кодонов), морфизм — пара «скалярная фаза из `K` + биекция
носителей». Такая пара — ровно то, что делает историческая формула

    σᵢ(xᵢ, xᵢ₊₁) = ω(xᵢ, xᵢ₊₁) · (xᵢ₊₁, xᵢ),

но на уровне позиций, без привязки к конкретным глифам.

**Что здесь строится конструктивно, а не аксиоматически.** `Category`
заполняется явными `id`/`comp` и доказательствами `id_comp`, `comp_id`,
`assoc`. Никаких `axiom`, `sorry` или «постулируем категорию».

**Чего здесь НЕТ.** Это не полная QCat: нет генераторов переписывания
`r_{y←x}`, нет памяти `δ`, `T`, `μ_δ`, нет `QCat₂L`. Фазовая таблица `ω`
здесь тоже не входит в морфизм: она зависит от меток на проводах и живёт
в `PhaseNaturality.lean` и в `QCatFormal.GeneralBraid`.
-/

open CategoryTheory

namespace QCat

/-- Объект брайд-ядра: тип-носитель меток. `carrier := PEmpty` — единица
    (0 кодонов), `carrier := α ⊕ β` — тензорное произведение. -/
structure BraidCore (K : Type) where
  carrier : Type

namespace BraidCore

variable {K : Type}

/-- Морфизм: фаза и биекция носителей. -/
structure Hom (X Y : BraidCore K) where
  /-- Скалярная фаза (в QCat — элемент `Q₋₁ˣ`). -/
  phase : K
  /-- Биекция носителей: перестановка позиций/меток. -/
  perm : X.carrier ≃ Y.carrier

@[ext]
theorem Hom.ext {X Y : BraidCore K} {f g : Hom X Y}
    (h1 : f.phase = g.phase) (h2 : f.perm = g.perm) : f = g := by
  cases f
  cases g
  simp_all

variable [CommMonoid K]

/-- **Категория `BraidCore K`.** `id` — фаза `1` и тождественная биекция;
    композиция — произведение фаз и композиция биекций. -/
instance instCategory : Category (BraidCore K) where
  Hom X Y := Hom X Y
  id X := ⟨1, Equiv.refl X.carrier⟩
  comp f g := ⟨f.phase * g.phase, f.perm.trans g.perm⟩
  id_comp f := by apply Hom.ext <;> simp
  comp_id f := by apply Hom.ext <;> simp
  assoc f g h := by apply Hom.ext <;> simp [mul_assoc, Equiv.trans_assoc]

@[simp]
theorem id_phase (X : BraidCore K) : (𝟙 X : Hom X X).phase = 1 := rfl

@[simp]
theorem id_perm (X : BraidCore K) : (𝟙 X : Hom X X).perm = Equiv.refl X.carrier := rfl

@[simp]
theorem comp_phase {X Y Z : BraidCore K} (f : X ⟶ Y) (g : Y ⟶ Z) :
    (f ≫ g).phase = f.phase * g.phase := rfl

@[simp]
theorem comp_perm {X Y Z : BraidCore K} (f : X ⟶ Y) (g : Y ⟶ Z) :
    (f ≫ g).perm = f.perm.trans g.perm := rfl

/-- Изоморфизм, построенный из биекции носителей с единичной фазой. -/
def isoOfEquiv {X Y : BraidCore K} (e : X.carrier ≃ Y.carrier) : Iso X Y where
  hom := ⟨1, e⟩
  inv := ⟨1, e.symm⟩
  hom_inv_id := by apply Hom.ext <;> simp
  inv_hom_id := by apply Hom.ext <;> simp

@[simp]
theorem isoOfEquiv_hom_phase {X Y : BraidCore K} (e : X.carrier ≃ Y.carrier) :
    (isoOfEquiv e).hom.phase = 1 := rfl

@[simp]
theorem isoOfEquiv_hom_perm {X Y : BraidCore K} (e : X.carrier ≃ Y.carrier) :
    (isoOfEquiv e).hom.perm = e := rfl

/-! ### Точная фазовая модель: `BraidCore Kˣ` (F4 аудита Илори)

Аудит `QCAT_CLOSURE_007_ILORI_AUDIT` (F4) отметил, что `Hom.phase : K`
допускает `0`, тогда как историческая фаза `ω : Σ × Σ → Q₋₁ˣ` живёт в
**единицах** кольца. Ответ здесь не «сузить структуру», а
**инстанцировать** её: `BraidCore Kˣ`.

`Kˣ` — коммутативная группа, следовательно коммутативный моноид,
поэтому все экземпляры (`Category`, `MonoidalCategory`,
`BraidedCategory`, `SymmetricCategory`) наследуются без изменений.
`BraidCore K` остаётся намеренно **широкой** оболочкой. -/

/-- Точная фазовая модель: фазы берутся из группы единиц `Kˣ`. -/
abbrev BraidCoreUnits (K : Type) [CommMonoid K] := BraidCore Kˣ

/-- В `BraidCore Kˣ` каждая фаза обратима — это и есть отличие от
    широкой оболочки `BraidCore K`. -/
theorem phase_isUnit {K : Type} [CommMonoid K] {X Y : BraidCoreUnits K}
    (f : X ⟶ Y) : IsUnit (f.phase : K) :=
  Units.isUnit f.phase

/-- Обратное включение: морфизм с обратимой фазой — изоморфизм.
    Значит изоморфизмы `BraidCore K` — ровно морфизмы единичной фазы,
    и `BraidCore Kˣ` — это в точности «фазово-обратимая часть». -/
theorem isIso_of_isUnit_phase {X Y : BraidCore K} (f : X ⟶ Y) (h : IsUnit f.phase) :
    IsIso f := by
  obtain ⟨v, hv⟩ := isUnit_iff_exists_inv.mp h
  have hv' : v * f.phase = 1 := by rw [mul_comm, hv]
  exact ⟨⟨⟨v, f.perm.symm⟩, by apply Hom.ext <;> simp [hv],
    by apply Hom.ext <;> simp [hv']⟩⟩

end BraidCore

end QCat
