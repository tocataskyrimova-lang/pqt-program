import QCatBraidCore.Monoidal
import Mathlib.CategoryTheory.Monoidal.Braided.Basic

/-!
# Сплетение на `BraidCore` (QCAT-CATEGORY-CLOSURE-007, п.3)

`β_ X Y` — биекция `X.carrier ⊕ Y.carrier ≃ Y.carrier ⊕ X.carrier`
(`Equiv.sumComm`) с **единичной** фазой.

**Почему фаза единичная.** Историческая `σᵢ(a,b) = ω(a,b)·(b,a)` состоит из
двух частей: перестановки проводов и скалярного множителя `ω`, зависящего
**от меток** на этих проводах. В `BraidCore` объект — это только носитель
(набор позиций), меток в нём нет, поэтому структурное сплетение несёт лишь
перестановку. Фаза `ω` добавляется отдельно и **не является** естественной
по отношению к произвольным переписываниям — это и есть содержание
`PhaseNaturality.lean` (п.4–5 задания). Здесь же доказывается, что
*перестановочная* часть — настоящая braided-структура.

**Конструктивность.** Все четыре условия (`braiding_naturality_left/right`,
`hexagon_forward`, `hexagon_reverse`) доказываются поточечно: после `ext`
и разбора вариантов `Sum` обе части — одна и та же функция. Никаких
`aesop_cat`, `axiom`, `sorry`.
-/

open CategoryTheory
open CategoryTheory.MonoidalCategory

namespace QCat
namespace BraidCore

variable {K : Type} [CommMonoid K]

/-- Сплетение: обмен двух слагаемых носителя, фаза `1`. -/
def braidingIso (X Y : BraidCore K) : X ⊗ Y ≅ Y ⊗ X :=
  isoOfEquiv (Equiv.sumComm X.carrier Y.carrier)

/-- **`BraidCore K` — брайд-моноидальная категория.** -/
instance instBraidedCategory : BraidedCategory (BraidCore K) where
  braiding := braidingIso
  braiding_naturality_right X {Y Z} f := by
    apply Hom.ext
    · simp [braidingIso]
    · ext x
      rcases x with (a | b) <;> rfl
  braiding_naturality_left {X Y} f Z := by
    apply Hom.ext
    · simp [braidingIso]
    · ext x
      rcases x with (a | b) <;> rfl
  hexagon_forward X Y Z := by
    apply Hom.ext
    · simp [braidingIso]
    · ext x
      rcases x with ((a | b) | c) <;> rfl
  hexagon_reverse X Y Z := by
    apply Hom.ext
    · simp [braidingIso]
    · ext x
      rcases x with (a | (b | c)) <;> rfl

/-! ### Проверки: сплетение — именно то, что ожидается -/

/-- Фаза сплетения равна `1`. -/
@[simp]
theorem braiding_phase (X Y : BraidCore K) : (β_ X Y).hom.phase = 1 := rfl

/-- Перестановка сплетения — `Equiv.sumComm`. -/
@[simp]
theorem braiding_perm (X Y : BraidCore K) :
    (β_ X Y).hom.perm = Equiv.sumComm X.carrier Y.carrier := rfl

/-- Сплетение действует на носителе как обмен: `inl a ↦ inr a`. -/
theorem braiding_apply_inl (X Y : BraidCore K) (a : X.carrier) :
    (β_ X Y).hom.perm (Sum.inl a) = Sum.inr a := rfl

/-- Сплетение действует на носителе как обмен: `inr b ↦ inl b`. -/
theorem braiding_apply_inr (X Y : BraidCore K) (b : Y.carrier) :
    (β_ X Y).hom.perm (Sum.inr b) = Sum.inl b := rfl

/-- Двойное сплетение возвращает носитель на место (по перестановке). -/
theorem braiding_perm_comp_self (X Y : BraidCore K) :
    (β_ X Y).hom.perm.trans (β_ Y X).hom.perm = Equiv.refl (X.carrier ⊕ Y.carrier) := by
  ext x
  rcases x with (a | b) <;> rfl

/-! ### Симметричность: F1 аудита Илори

Аудит `QCAT_CLOSURE_007_ILORI_AUDIT` (F1) указал, что `β_` с перестановкой
`Equiv.sumComm` и фазой `1` симметрично **как полный морфизм**, а не только
как перестановка. Здесь это фиксируется теоремой и, что важнее, —
экземпляром `SymmetricCategory`, то есть попадает в **тип**, а не в
комментарий.

Следствие для претензий проекта: `BraidCore` — симметрическая модель.
Несимметрический фазовый braiding исторической QCat (`ω(a,b)ω(b,a) ≠ 1`)
здесь **не** представлен: `ω` в `instBraidedCategory` не входит. -/

/-- **F1.** `(β_ X Y).hom ≫ (β_ Y X).hom = 𝟙 (X ⊗ Y)` — с фазами. -/
theorem braiding_double_eq_id (X Y : BraidCore K) :
    (β_ X Y).hom ≫ (β_ Y X).hom = 𝟙 (X ⊗ Y) := by
  apply Hom.ext
  · simp
  · simpa using braiding_perm_comp_self X Y

/-- **`BraidCore K` — симметрическая моноидальная категория.**
    Это утверждение в типе класса, а не в документации. -/
instance instSymmetricCategory : SymmetricCategory (BraidCore K) where
  symmetry := braiding_double_eq_id

end BraidCore
end QCat
