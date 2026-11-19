import Mathlib.Algebra.Group.Basic

/-!
# Брейд-соотношения исторического QCat: B1 и обратимость

**Первоисточник** `QMath_v3.md`, §3 «Braid relations» (строки 112–155):

* **(B1) Local commutativity** — `σᵢ σⱼ = σⱼ σᵢ` при `|i−j| > 1`
  (в документе это B1, строка 116);
* **(B2) Yang–Baxter relation** — `σᵢ σᵢ₊₁ σᵢ = σᵢ₊₁ σᵢ σᵢ₊₁`
  (в документе это B2, строка 136).

B2 для фазово-перестановочного брейдинга доказано в `Historical.lean`
(`QCat.Historical.yang_baxter`). Здесь закрываются два других пробела:

1. **B1** — требует слова длины 4 (σ₁ и σ₃ действуют на непересекающиеся
   позиции); в `Historical.lean` модель была длины 3, поэтому B1 там
   вообще не формулировалась.
2. **Обратимость σᵢ** — в первичном тексте фазы лежат в `Q₋₁ˣ`, т.е.
   обратимы. При `[CommGroup K]` явно строится `σ⁻¹` и проверяются оба
   равенства `σ⁻¹σ = id` и `σσ⁻¹ = id`.

Как и в `Historical.lean`, метки базиса не меняются (переставляются только
позиции), накапливается скалярная фаза. Никаких `sorry` и новых аксиом.
-/

namespace QCat.BraidRelations

abbrev Glyph := Fin 4

/-- Слово длины 4. `×` правоассоциативно: `(a, (b, (c, d)))`. -/
abbrev Quad := Glyph × Glyph × Glyph × Glyph

/-- Слово длины 3 (как в `Historical.lean`). -/
abbrev Triple := Glyph × Glyph × Glyph

abbrev Scaled4 (K : Type*) := K × Quad
abbrev Scaled3 (K : Type*) := K × Triple

/-- Фазовая таблица `ω : Σ × Σ → K`, тип параметра задан явно. -/
abbrev PhaseTable (K : Type*) := Glyph → Glyph → K

section B1

variable {K : Type*} [CommMonoid K]

/-- σ₁: перестановка позиций 1 и 2 с фазой `ω(a,b)`. -/
def sigma1 (omega : PhaseTable K) (s : Scaled4 K) : Scaled4 K :=
  (s.1 * omega s.2.1 s.2.2.1,
   (s.2.2.1, s.2.1, s.2.2.2))

/-- σ₃: перестановка позиций 3 и 4 с фазой `ω(c,d)`. -/
def sigma3 (omega : PhaseTable K) (s : Scaled4 K) : Scaled4 K :=
  (s.1 * omega s.2.2.2.1 s.2.2.2.2,
   (s.2.1, s.2.2.1, (s.2.2.2.2, s.2.2.2.1)))

/-- **B1 (Local commutativity).** σ₁ и σ₃ коммутируют при любых фазах:
    они действуют на непересекающиеся пары позиций, а `K` коммутативен.
    Обратимость ω не нужна. -/
theorem local_commutativity_B1 (omega : PhaseTable K) (s : Scaled4 K) :
    sigma1 omega (sigma3 omega s) = sigma3 omega (sigma1 omega s) := by
  rcases s with ⟨k, w⟩
  rcases w with ⟨a, q⟩
  rcases q with ⟨b, r⟩
  rcases r with ⟨c, d⟩
  simp [sigma1, sigma3, mul_assoc, mul_comm, mul_left_comm]

end B1

section Inverse

variable {K : Type*} [CommGroup K]

/-- σ₁₂ на слове длины 3 (совпадает с `QCat.Historical.sigma12`). -/
def sigma12 (omega : PhaseTable K) (s : Scaled3 K) : Scaled3 K :=
  (s.1 * omega s.2.1 s.2.2.1,
   (s.2.2.1, s.2.1, s.2.2.2))

/-- Обратный брейдинг: делим на ту же фазу `ω(x,y)`, извлекая `x,y`
    из уже переставленного слова `(y,x,z)`. -/
def sigma12Inv (omega : PhaseTable K) (s : Scaled3 K) : Scaled3 K :=
  (s.1 * (omega s.2.2.1 s.2.1)⁻¹,
   (s.2.2.1, s.2.1, s.2.2.2))

/-- `σ⁻¹ ∘ σ = id`: для существования обратного достаточно `[CommGroup K]`,
    симметричность (`ω(x,y)ω(y,x)=1`) не требуется. -/
theorem sigma12Inv_sigma12 (omega : PhaseTable K) (s : Scaled3 K) :
    sigma12Inv omega (sigma12 omega s) = s := by
  rcases s with ⟨k, w⟩
  rcases w with ⟨x, y, z⟩
  simp [sigma12, sigma12Inv]

/-- `σ ∘ σ⁻¹ = id`. -/
theorem sigma12_sigma12Inv (omega : PhaseTable K) (s : Scaled3 K) :
    sigma12 omega (sigma12Inv omega s) = s := by
  rcases s with ⟨k, w⟩
  rcases w with ⟨x, y, z⟩
  simp [sigma12, sigma12Inv]

/-- Обратимость fase сама по себе: `ω(x,y) · (ω(x,y))⁻¹ = 1`.
    Отдельно от симметричности, которая даёт `ω(x,y)⁻¹ = ω(y,x)`. -/
theorem phase_has_inverse (omega : PhaseTable K) (x y : Glyph) :
    omega x y * (omega x y)⁻¹ = 1 := by
  simp

end Inverse

end QCat.BraidRelations

-- Аудит аксиом: ни одна теорема не должна тянуть `sorryAx`.
#print axioms QCat.BraidRelations.local_commutativity_B1
#print axioms QCat.BraidRelations.sigma12Inv_sigma12
#print axioms QCat.BraidRelations.sigma12_sigma12Inv
#print axioms QCat.BraidRelations.phase_has_inverse
