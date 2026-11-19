import Mathlib.LinearAlgebra.Finsupp.LSum
import Mathlib.Data.Finsupp.Single
import Mathlib.Algebra.Group.Basic

/-!
# Линейная фазовая модель на свободном модуле (QLP-02)

`Historical.lean` проверяет соотношения на **одном** базисном мономе
`(coeff, word)`. Аудит Илори справедливо указал, что это ещё не
«представление на свободном `K`-модуле». Здесь строится буквальная линейная
модель:

* носитель — `Triple →₀ K`, свободный `K`-модуль с базисом из слов длины 3;
* `σ₁₂`, `σ₂₃` определены как **`K`-линейные отображения** через
  `Finsupp.lsum`: базисный вектор `e_w` переходит в `ω(w)·e_{perm w}`;
* YBE доказывается сначала на базисных векторах, затем переносится на весь
  модуль индукцией `Finsupp.induction_linear` (аддитивность + однородность).

Так снимается замечание QLP-02: утверждение «представление на свободном
модуле проверено» теперь корректно в объёме `K`-линейной модели.

**Границы (`not_claimed`).** Это по-прежнему не `Category`/`MonoidalCategory`/
`BraidedCategory QCat`: нет объектов-натуральных чисел, тензорного произведения
как функтора, гексагонов и естественности braiding. Модуль даёт только
линейный оператор σ на фиксированной длине 3.
-/

namespace QCat.FreeModule

/-- Четыре глифа `Σ = {α, β, γ, δ}`. -/
abbrev Glyph := Fin 4

/-- Слово длины 3. `×` правоассоциативно: `(x, (y, z))`. -/
abbrev Triple := Glyph × Glyph × Glyph

/-- Фазовая таблица `ω : Σ × Σ → K`. -/
abbrev PhaseTable (K : Type*) := Glyph → Glyph → K

/-- Перестановка позиций 1 и 2. -/
def swap12 (w : Triple) : Triple := (w.2.1, w.1, w.2.2)

/-- Перестановка позиций 2 и 3. -/
def swap23 (w : Triple) : Triple := (w.1, w.2.2, w.2.1)

/-- Фаза σ₁₂ на слове `w = (x,y,z)`. -/
def phase12 {K : Type*} (omega : PhaseTable K) (w : Triple) : K := omega w.1 w.2.1

/-- Фаза σ₂₃ на слове `w = (x,y,z)`. -/
def phase23 {K : Type*} (omega : PhaseTable K) (w : Triple) : K := omega w.2.1 w.2.2

section Linear

variable {K : Type*} [CommSemiring K]

-- `Finsupp.single` в этой связке невычислим: помечаем весь линейный слой
-- `noncomputable`. Теоремы — `Prop`, на проверку ядром это не влияет.
noncomputable section

/-- Базисный образ `e_w ↦ (phase w) • e_{perm w}` как `K`-линейное
    отображение `K →ₗ[K] (Triple →₀ K)`. -/
def basisImage (perm : Triple → Triple) (phase : Triple → K) (w : Triple) :
    K →ₗ[K] (Triple →₀ K) where
  toFun := fun c => Finsupp.single (perm w) (phase w * c)
  map_add' := by
    intro a b
    ext t
    by_cases h : perm w = t
    · simp [h, mul_add]
    · simp [Finsupp.single_apply, h]
  map_smul' := by
    intro c x
    ext t
    by_cases h : perm w = t
    · simp [h, mul_assoc, mul_comm, mul_left_comm]
    · simp [Finsupp.single_apply, h]

/-- **σ₁₂ как линейное отображение свободного модуля.** -/
def sigma12Lin (omega : PhaseTable K) : (Triple →₀ K) →ₗ[K] (Triple →₀ K) :=
  Finsupp.lsum K (basisImage swap12 (phase12 omega))

/-- **σ₂₃ как линейное отображение свободного модуля.** -/
def sigma23Lin (omega : PhaseTable K) : (Triple →₀ K) →ₗ[K] (Triple →₀ K) :=
  Finsupp.lsum K (basisImage swap23 (phase23 omega))

/-- Действие σ₁₂ на произвольный элемент модуля — это сумма по носителю,
    то есть отображение задано на **всём** модуле, а не только на мономах. -/
theorem sigma12Lin_apply (omega : PhaseTable K) (v : Triple →₀ K) :
    sigma12Lin omega v =
      v.sum (fun w c => Finsupp.single (swap12 w) (phase12 omega w * c)) :=
  rfl

theorem sigma23Lin_apply (omega : PhaseTable K) (v : Triple →₀ K) :
    sigma23Lin omega v =
      v.sum (fun w c => Finsupp.single (swap23 w) (phase23 omega w * c)) :=
  rfl

/-- Значение на базисном векторе. -/
theorem sigma12Lin_single (omega : PhaseTable K) (w : Triple) (c : K) :
    sigma12Lin omega (Finsupp.single w c) =
      Finsupp.single (swap12 w) (phase12 omega w * c) := by
  simp [sigma12Lin, basisImage, Finsupp.lsum_single]

theorem sigma23Lin_single (omega : PhaseTable K) (w : Triple) (c : K) :
    sigma23Lin omega (Finsupp.single w c) =
      Finsupp.single (swap23 w) (phase23 omega w * c) := by
  simp [sigma23Lin, basisImage, Finsupp.lsum_single]

/-- YBE на одном базисном векторе: сводится к коммутативности `K`. -/
theorem yang_baxter_single (omega : PhaseTable K) (w : Triple) (c : K) :
    sigma12Lin omega (sigma23Lin omega (sigma12Lin omega (Finsupp.single w c))) =
      sigma23Lin omega (sigma12Lin omega (sigma23Lin omega (Finsupp.single w c))) := by
  rcases w with ⟨x, y, z⟩
  simp [sigma12Lin_single, sigma23Lin_single, phase12, phase23, swap12, swap23,
    mul_assoc, mul_comm, mul_left_comm]

/-- **YBE на всём свободном `K`-модуле.** Перенос с базиса по линейности:
    `Finsupp.induction_linear` (нуль, сумма, базисный вектор). -/
theorem yang_baxter (omega : PhaseTable K) (v : Triple →₀ K) :
    sigma12Lin omega (sigma23Lin omega (sigma12Lin omega v)) =
      sigma23Lin omega (sigma12Lin omega (sigma23Lin omega v)) := by
  let p : (Triple →₀ K) → Prop := fun v =>
    sigma12Lin omega (sigma23Lin omega (sigma12Lin omega v)) =
      sigma23Lin omega (sigma12Lin omega (sigma23Lin omega v))
  change p v
  refine Finsupp.induction_linear v ?h0 ?hadd ?hsingle
  · simp [p]
  · intro f g hf hg
    simp only [p, map_add, hf, hg]
  · intro w c
    exact yang_baxter_single omega w c

/-- σ₁₂ линеен по определению — проверка, что это не только функция на
    мономах (склейка суммы). -/
theorem sigma12Lin_add (omega : PhaseTable K) (v w : Triple →₀ K) :
    sigma12Lin omega (v + w) = sigma12Lin omega v + sigma12Lin omega w :=
  map_add _ _ _

theorem sigma12Lin_smul (omega : PhaseTable K) (c : K) (v : Triple →₀ K) :
    sigma12Lin omega (c • v) = c • sigma12Lin omega v :=
  map_smul _ _ _

/-- Двойное применение σ₁₂ на мономе: метки возвращаются, накапливается
    монодромия `ω(x,y)·ω(y,x)`. -/
theorem sigma12Lin_sq_single (omega : PhaseTable K) (c : K) (x y z : Glyph) :
    sigma12Lin omega (sigma12Lin omega (Finsupp.single (x, y, z) c)) =
      Finsupp.single (x, y, z) (c * (omega x y * omega y x)) := by
  simp [sigma12Lin_single, phase12, swap12, mul_assoc, mul_comm, mul_left_comm]

end

end Linear

end QCat.FreeModule
