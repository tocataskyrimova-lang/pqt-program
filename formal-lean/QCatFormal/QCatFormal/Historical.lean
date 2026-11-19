import Mathlib.Algebra.Group.Basic
import QCatFormal.Scope

/-!
# Исторический QCat: фазово-перестановочный брейдинг σᵢ (этап 1bis)

**Первоисточник.** `QMath_v3.md` (PQT-AUDIT-001/PQT-007/.../sources):

    σ_i(x_i, x_{i+1}) = ω(x_i, x_{i+1}) · (x_{i+1}, x_i),
    ω : Σ × Σ → Q₋₁ˣ.

Это **не** диэдральная модель `R(a,b) = (b, 2b − a) mod 64` из `RMap.lean`:
здесь метки базиса не меняются, меняется только порядок позиций и
накапливается скалярная фаза. `RMap.lean` — независимая альтернативная
модель, её выводы о естественности автоматически не переносятся сюда.

**Модель в этом файле.** Берём свободный `K`-модуль с базисом из слов
длины 3 над `Σ = {α,β,γ,δ}` и представляем базисный вектор с коэффициентом
парой `(coeff, word)`. Линейность позволяет проверять braid-соотношения на
базисных векторах. `K` — произвольный коммутативный моноид: это ровно то,
что нужно для YBE; обратимость фаз понадобится только для того, чтобы σᵢ
был изоморфизмом.

**QLP-01: область провода.** Здесь явно выбрано `scope_of_wire = glyph`:
`ω : Σ × Σ → K`, слово — тройка глифов. Это **не** полное кодонное
представление (`Σ³` как единый объект): кодонный вариант требует подъёма
таблицы 4 → 64, который первоисточник не фиксирует (`Scope.lean`).
Линейная версия на `Triple →₀ K` — в `FreeModule.lean` (QLP-02).

**Результаты (по замечанию Хикса, 2026-11-07):**
* YBE выполняется для **любой** таблицы ω, обратимость не нужна
  (коммутативность K; финальное слово в обеих цепочках — `(z,y,x)`).
* `σ² = id` ⇔ `ω(x,y)·ω(y,x) = 1` для всех x,y.
* Если произведение ≠ 1, брейдинг несимметричен **без смены меток кодонов**;
  обратно, из `ω(x,y)·ω(y,x)=1` следует обратимость ω(x,y)
  (обратный — ω(y,x)).

Никаких `sorry`, новых аксиом и не проверенных ядром допущений.
-/

namespace QCat.Historical

/-- **QLP-01:** область провода, явно выбранная в этой модели — **глифы**.
    То есть σ здесь действует на тройку глифов, а не на два полных кодона
    из `Σ³`. Это честная частичная модель; кодонный вариант требует
    отдельного лифтинга (`QCat.Scope.codonFirst` / `codonLast`), и
    первоисточник этот лифтинг не фиксирует. -/
def scope_of_wire : QCat.Scope.WireScope := QCat.Scope.WireScope.glyph

theorem scope_of_wire_eq : scope_of_wire = QCat.Scope.WireScope.glyph := rfl

/-- Четыре глифа `Σ = {α, β, γ, δ}`. -/
abbrev Glyph := Fin 4

/-- Слово длины 3. `×` правоассоциативно: `(x, (y, z))`. -/
abbrev Triple := Glyph × Glyph × Glyph

/-- **Один базисный моном** `c · e_w`, то есть пара `(коэффициент, слово)`.
    Это НЕ элемент свободного модуля: конечные суммы таких мономов образуют
    `Triple →₀ K` (см. `FreeModule.lean`, QLP-02). Имя `Scaled` сохранено
    ради совместимости, но семантика — «моном», а не «вектор». -/
abbrev Scaled (K : Type*) := K × Triple

/-- Фазовая таблица исторического QCat: `ω : Σ × Σ → K`.
    В каноне `K = Q₋₁ˣ`; здесь она параметризована явно, чтобы тип
    коэффициента выводился однозначно. -/
abbrev PhaseTable (K : Type*) := Glyph → Glyph → K

section PhaseFlip

variable {K : Type*} [CommMonoid K]

/-- σ₁₂: перестановка позиций 1 и 2 с умножением на ω(x,y). -/
def sigma12 (omega : PhaseTable K) (s : Scaled K) : Scaled K :=
  (s.1 * omega s.2.1 s.2.2.1,
   (s.2.2.1, s.2.1, s.2.2.2))

/-- σ₂₃: перестановка позиций 2 и 3 с умножением на ω(y,z). -/
def sigma23 (omega : PhaseTable K) (s : Scaled K) : Scaled K :=
  (s.1 * omega s.2.2.1 s.2.2.2,
   (s.2.1, s.2.2.2, s.2.2.1))

/-- Явные фазы двух путей в YBE (для сверки с `QMath_v3.md` **B2**, строка 136;
    B1 — это local commutativity, строка 116, см. `BraidRelations`/`GeneralBraid`). -/
theorem left_path (omega : PhaseTable K) (c : K) (x y z : Glyph) :
    sigma12 omega (sigma23 omega (sigma12 omega (c, (x, y, z)))) =
      (((c * omega x y) * omega x z) * omega y z, (z, y, x)) := by
  rfl

theorem right_path (omega : PhaseTable K) (c : K) (x y z : Glyph) :
    sigma23 omega (sigma12 omega (sigma23 omega (c, (x, y, z)))) =
      (((c * omega y z) * omega x z) * omega x y, (z, y, x)) := by
  rfl

/-- **Yang–Baxter для исторического QCat (B2).** Следует из коммутативности K,
    обратимость ω не требуется. Machine-checked версия **B2** из первичного
    текста (`QMath_v3.md:136`) для фазово-перестановочного брейдинга.
    Не путать с **B1** (`QMath_v3.md:116`, local commutativity) — она
    формализована отдельно в `BraidRelations.local_commutativity_B1`
    и `GeneralBraid.local_commutativity_general`. -/
theorem yang_baxter (omega : PhaseTable K) (s : Scaled K) :
    sigma12 omega (sigma23 omega (sigma12 omega s)) =
      sigma23 omega (sigma12 omega (sigma23 omega s)) := by
  rcases s with ⟨c, w⟩
  rcases w with ⟨x, y, z⟩
  rw [left_path, right_path]
  simp [mul_assoc, mul_comm, mul_left_comm]

/-- Двукратное применение σ₁₂ возвращает исходное слово, но накапливает
    монодромию `ω(x,y)·ω(y,x)`. -/
theorem sigma12_sq (omega : PhaseTable K) (c : K) (x y z : Glyph) :
    sigma12 omega (sigma12 omega (c, (x, y, z))) =
      (c * (omega x y * omega y x), (x, y, z)) := by
  simp [sigma12, mul_assoc]

/-- На метках σ всегда инволюция — независимо от фаз. Ключевое отличие
    от диэдральной R, у которой порядок на метках равен 64. -/
theorem label_involutive (omega : PhaseTable K) (c : K) (x y z : Glyph) :
    (sigma12 omega (sigma12 omega (c, (x, y, z)))).2 = (x, y, z) := by
  rfl

/-- Условие симметричности, как в первичном тексте и в правке Хикса. -/
def HasUnitMonodromy (omega : PhaseTable K) : Prop :=
  ∀ x y : Glyph, omega x y * omega y x = 1

/-- Инволютивность брейдинга (включая коэффициент). -/
def IsSymmetric (omega : PhaseTable K) : Prop :=
  ∀ s : Scaled K, sigma12 omega (sigma12 omega s) = s

/-- **σ² = id ⇔ ω(x,y)·ω(y,x) = 1.** -/
theorem symmetric_iff_unit_monodromy (omega : PhaseTable K) :
    IsSymmetric omega ↔ HasUnitMonodromy omega := by
  constructor
  · intro h x y
    have hh := congrArg Prod.fst (h ((1 : K), (x, y, (0 : Glyph))))
    simpa [sigma12, mul_assoc] using hh
  · intro h s
    rcases s with ⟨c, w⟩
    rcases w with ⟨x, y, z⟩
    simp [sigma12, mul_assoc, h x y]

/-- Если монодромия не единична, брейдинг несимметричен при неизменных метках. -/
theorem nonsymmetric_without_relabelling (omega : PhaseTable K)
    (x y : Glyph) (h : omega x y * omega y x ≠ 1) :
    ¬ IsSymmetric omega := by
  intro hs
  exact h ((symmetric_iff_unit_monodromy omega).mp hs x y)

/-- Из симметричности обратимость фазы следует автоматически:
    обратный к ω(x,y) — ω(y,x). -/
theorem symmetric_gives_inverse (omega : PhaseTable K)
    (h : HasUnitMonodromy omega) (x y : Glyph) :
    omega x y * omega y x = 1 ∧ omega y x * omega x y = 1 :=
  ⟨h x y, by simpa [mul_comm] using h y x⟩

/-- Постоянная фаза r симметрична ⇔ r² = 1. -/
theorem constant_phase_symmetric_iff (r : K) :
    HasUnitMonodromy (fun (_ : Glyph) (_ : Glyph) => r) ↔ r * r = 1 := by
  constructor
  · intro h
    exact h 0 0
  · intro h x y
    exact h

end PhaseFlip

end QCat.Historical
