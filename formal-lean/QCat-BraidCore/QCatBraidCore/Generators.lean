import QCatBraidCore.PhaseNaturality
import Mathlib.Data.Fin.VecNotation
import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Fintype.Prod
import Mathlib.Data.Fintype.Card

/-!
# Реестр исторических генераторов (QCAT-CATEGORY-CLOSURE-007, п.6)

Источник: `PQT_QCAT_FINITE_PRESENTATION_INDEPENDENCE_MODELS_v0.1_RU.md`

* §2.2, строки 125–140 — **rewrite generators**:
  для каждой упорядоченной пары `x ≠ y` генератор `r_{y←x} : x → y`,
  всего `4 · 3 = 12`. Отношение `r_{z←y} ∘ r_{y←x} = r_{z←x}`
  **не** постулируется.
* §2.3, строки 141–152 — **braiding generators**:
  для `x, y ∈ Σ` компонент `b_{x,y} : x ⊗ y → y ⊗ x`, всего `16`.

Здесь эти семейства оформлены как **данные** (`Finset`/типы с `Fintype`),
а не как утверждения: реестр нужен, чтобы последующая проверка
многоместной naturality ссылалась на конкретный конечный список,
а не на «все пары» из текста.

**Чего здесь НЕТ.** Никакой проверки многоместной naturality не проводится.
`MultiPlacePhaseNatural` — это **определение требования** (шаблон),
а не теорема. Никаких утверждений о памяти, `Witness`, `QCat₂L`,
физике.
-/

namespace QCat
namespace Generators

/-! ### Алфавит -/

/-- Алфавит глифов `Σ = {0, 1, 2, 3}` (четыре буквы кодового алфавита). -/
abbrev Glyph : Type := Fin 4

theorem card_glyph : Fintype.card Glyph = 4 := rfl

/-! ### §2.2. Rewrite generators `r_{y←x}`, `x ≠ y` -/

/-- Реестр генераторов переписывания: упорядоченная пара `(x, y)` с `x ≠ y`. -/
abbrev RewriteGen : Type := {p : Glyph × Glyph // p.1 ≠ p.2}

instance : Fintype RewriteGen :=
  Fintype.subtype (Finset.univ.filter (fun p : Glyph × Glyph => p.1 ≠ p.2))
    (by intro p; simp)

/-- Все 12 генераторов переписывания одним списком. -/
def rewriteGenerators : Finset (Glyph × Glyph) :=
  Finset.univ.filter (fun p : Glyph × Glyph => p.1 ≠ p.2)

/-- §2.2: число генераторов `4 · 3 = 12`. -/
theorem card_rewriteGenerators : rewriteGenerators.card = 12 := by decide

/-- То же через `Fintype.card`. -/
theorem card_rewriteGen : Fintype.card RewriteGen = 12 := by decide

/-- **Модель** генератора `r_{y←x}` глобальной функцией (`x ↦ y`, остальное
    на месте).

    Это интерпретация, а не определение генератора (F3 аудита Илори):
    исторический `r_{y←x}` — типизированная стрелка `[x] ⟶ [y]`, см.
    `Typed.Rewrite`. Переход «стрелка → функция» оформлен отдельно как
    `Typed.modelOf`, и там доказано, что он верен
    (`Typed.modelOf_injective`) и не добавляет соотношений
    (`Typed.modelOf_comp_not_eq`). -/
def rewriteGenFun (g : RewriteGen) : Glyph → Glyph :=
  PhaseNaturality.replace g.1.1 g.1.2

/-- `r_{y←x}` действительно переводит `x` в `y`. -/
@[simp]
theorem rewriteGenFun_src (g : RewriteGen) : rewriteGenFun g g.1.1 = g.1.2 := by
  simp [rewriteGenFun]

/-- `r_{y←x}` не трогает глифы, отличные от `x`. -/
theorem rewriteGenFun_of_ne (g : RewriteGen) {a : Glyph} (h : a ≠ g.1.1) :
    rewriteGenFun g a = a := by
  simp [rewriteGenFun, h]

/-! ### §2.3. Braiding generators `b_{x,y}` -/

/-- Реестр цветных компонентов сплетения: пара `(x, y)` без ограничений. -/
abbrev BraidingGen : Type := Glyph × Glyph

instance : Fintype BraidingGen := inferInstance

/-- Все 16 цветных компонентов одним списком. -/
def braidingComponents : Finset BraidingGen := Finset.univ

/-- §2.3: компонентов `4 · 4 = 16`. -/
theorem card_braidingComponents : braidingComponents.card = 16 := by decide

/-- То же через `Fintype.card`. -/
theorem card_braidingGen : Fintype.card BraidingGen = 16 := by decide

/-- Компонент `b_{x,y}` как перестановка пары: `(x, y) ↦ (y, x)`. -/
def braidingGenSwap (g : BraidingGen) : Glyph × Glyph := (g.2, g.1)

/-- Двойной обмен возвращает пару на место. -/
theorem braidingGenSwap_involutive (g : BraidingGen) :
    braidingGenSwap (braidingGenSwap g) = g := rfl

/-! ### Шаблон для многоместной naturality (НЕ доказательство) -/

/-- Слово длины `n` над алфавитом глифов: `Σⁿ`. -/
abbrev Word (n : Nat) : Type := Fin n → Glyph

/-- **Требование** многоместной фазовой естественности: переписывание `f`
    на позиции `i` не меняет фазу слова. Это определение, а не теорема;
    проверка для конкретных `ω` — предмет следующего этапа. -/
def MultiPlacePhaseNatural {K : Type} (n : Nat) (ω : Word n → K)
    (i : Fin n) (f : Glyph → Glyph) : Prop :=
  ∀ w : Word n, ω (Function.update w i (f (w i))) = ω w

/-- Фазовая таблица на словах длины 2, индуцированная бинарной таблицей. -/
def wordPhase2 {K : Type} (ω : Glyph → Glyph → K) (w : Word 2) : K := ω (w 0) (w 1)

/-- **Мост к п.4.** Для `n = 2` и `i = 0` многоместное требование —
    это ровно `PhaseNaturalLeft` из `PhaseNaturality.lean`.
    Тем самым шаблон согласован с уже доказанным бинарным критерием. -/
theorem multiPlace_two_left_iff {K : Type} (ω : Glyph → Glyph → K) (f : Glyph → Glyph) :
    MultiPlacePhaseNatural 2 (wordPhase2 ω) 0 f ↔ PhaseNaturality.PhaseNaturalLeft ω f := by
  constructor
  · intro h a b
    have := h ![a, b]
    simpa [MultiPlacePhaseNatural, wordPhase2] using this
  · intro h w
    exact h (w 0) (w 1)

/-- Аналогичный мост для `i = 1` и правого аргумента. -/
theorem multiPlace_two_right_iff {K : Type} (ω : Glyph → Glyph → K) (f : Glyph → Glyph) :
    MultiPlacePhaseNatural 2 (wordPhase2 ω) 1 f ↔ PhaseNaturality.PhaseNaturalRight ω f := by
  constructor
  · intro h a b
    have := h ![a, b]
    simpa [MultiPlacePhaseNatural, wordPhase2] using this
  · intro h w
    exact h (w 0) (w 1)

end Generators
end QCat
