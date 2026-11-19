import Std

/-!
# Граница области ω: глифы Σ или полные кодоны Σ³? (этап 2bis + QLP-01)

`QMath_v3.md` задаёт `ω : Σ × Σ → Q₋₁ˣ`, но объекты QCat — это слова/кодоны,
и в каноне v3.4 `𝒞 := Σ³` (64 кодона). Первичные тексты **не определяют**,
на чём именно задана фазовая таблица: на 4 глифах (16 пар) или на 64 кодонах
(4096 пар). Это развилка, а не техническая деталь:

* если `ω` на Σ, то таблица имеет 16 степеней свободы;
* если `ω` на Σ³, то 4096, и при переходе Σ → Σ³ появляется дополнительный
  произвол (какой лифтинг выбрать — по первому глифу, по последнему, по
  свёртке и т.д.). Документы лифтинг не фиксируют.

**QLP-01 (аудит Илори).** Раньше уровень был выбран неявно: `Historical.lean`
брал `Glyph := Fin 4`, то есть молча работал на глифах. Теперь область провода
зафиксирована **явно**:

* `WireScope` — `glyph | codon`;
* `PhaseTable` — структура с полем `scope : WireScope`, обеими таблицами и
  доказанным согласием на диагональных глифовых парах;
* `scope_of_wire` — значение, выбранное в этой модели (`glyph`);
* `liftFirst` / `liftLast` — два разных подъёма 4 → 64.

**Что доказано здесь (только ядро Lean + `Std`, без Mathlib).**
1. `restrict ∘ liftFirst = id` и `restrict ∘ liftLast = id`: оба лифтинга
   согласованы с глифовой таблицей на диагонали `embed g = (g,g,g)`.
2. `liftFirst ≠ liftLast`: лифтинг не единственен.
3. Существуют две кодонные таблицы, **совпадающие на всех 16 глифовых парах**
   и различающиеся на паре кодонов вне диагонали ⇒ знание ω на Σ не
   определяет ω на Σ³.
4. `codon_scope_undetermined`: две `PhaseTable` с одинаковым `glyphPhase`,
   одинаковым `scope = codon` и **разными** `codonPhase`. Это и есть
   формальная фиксация того, что первоисточник не определяет уровень.

Вывод: утверждения о «полной классификации допустимых переписываний» должны
явно указывать уровень (Σ или Σ³). Без этого перенос результатов с одного
уровня на другой не обоснован. Мы не выдаём ни одну из интерпретаций за
«оригинальную QCat» — это зафиксированная неопределённость первичных текстов.
-/

namespace QCat.Scope

/-- `Σ = {α, β, γ, δ}`. -/
abbrev Glyph := Fin 4

/-- `𝒞 = Σ³`, 64 кодона. `×` правоассоциативно. -/
abbrev Codon := Glyph × Glyph × Glyph

/-- Конечная абстракция кольца фаз: достаточно двух различных значений,
    чтобы показать неединственность лифтинга. -/
abbrev Phase := Bool

/-- **QLP-01:** область, на которой задана фазовая таблица. -/
inductive WireScope where
  /-- Таблица на 4 глифах: 16 пар. -/
  | glyph
  /-- Таблица на 64 кодонах `Σ³`: 4096 пар. -/
  | codon
  deriving DecidableEq, Repr

/-- Носитель фазы при выбранной области. -/
def WireType : WireScope → Type
  | .glyph => Glyph
  | .codon => Codon

/-- Диагональное вложение глифа в кодон `(g,g,g)`. -/
def embed (g : Glyph) : Codon := (g, g, g)

def firstGlyph (c : Codon) : Glyph := c.1
def lastGlyph (c : Codon) : Glyph := c.2.2

/-- Политика подъёма: какой глиф кодона считается носителем фазы. -/
inductive LiftPolicy where
  | first
  | last
  deriving DecidableEq, Repr

/-- Лифтинг «по первому глифу кодона». -/
def liftFirst (omega : Glyph → Glyph → Phase) : Codon → Codon → Phase :=
  fun c d => omega (firstGlyph c) (firstGlyph d)

/-- Лифтинг «по последнему глифу кодона». -/
def liftLast (omega : Glyph → Glyph → Phase) : Codon → Codon → Phase :=
  fun c d => omega (lastGlyph c) (lastGlyph d)

/-- Общий лифтинг по явной политике. -/
def liftWith (policy : LiftPolicy) (omega : Glyph → Glyph → Phase) :
    Codon → Codon → Phase :=
  match policy with
  | .first => liftFirst omega
  | .last => liftLast omega

/-- Ограничение кодонной таблицы на диагональные глифовые пары. -/
def restrict (Omega : Codon → Codon → Phase) : Glyph → Glyph → Phase :=
  fun x y => Omega (embed x) (embed y)

/-- **QLP-01:** полная фазовая таблица с явно зафиксированной областью.
    Поле `compatible` — обещание, что кодонная таблица согласована с глифовой
    на диагонали; оно не утверждает, что лифтинг единственен. -/
structure PhaseTable where
  scope : WireScope
  glyphPhase : Glyph → Glyph → Phase
  codonPhase : Codon → Codon → Phase
  compatible : ∀ x y : Glyph, codonPhase (embed x) (embed y) = glyphPhase x y

/-- Таблица, в которой провод объявлен глифовым. -/
def glyphOnly (omega : Glyph → Glyph → Phase) : PhaseTable where
  scope := .glyph
  glyphPhase := omega
  codonPhase := liftFirst omega
  compatible := fun _ _ => rfl

/-- Кодонная таблица, поднятая по первому глифу. -/
def codonFirst (omega : Glyph → Glyph → Phase) : PhaseTable where
  scope := .codon
  glyphPhase := omega
  codonPhase := liftFirst omega
  compatible := fun _ _ => rfl

/-- Кодонная таблица, поднятая по последнему глифу. -/
def codonLast (omega : Glyph → Glyph → Phase) : PhaseTable where
  scope := .codon
  glyphPhase := omega
  codonPhase := liftLast omega
  compatible := fun _ _ => rfl

theorem restrict_liftFirst (omega : Glyph → Glyph → Phase) (x y : Glyph) :
    restrict (liftFirst omega) x y = omega x y := by
  rfl

theorem restrict_liftLast (omega : Glyph → Glyph → Phase) (x y : Glyph) :
    restrict (liftLast omega) x y = omega x y := by
  rfl

/-- Конкретная глифовая таблица и кодоны для свидетельства различия. -/
def omegaTest : Glyph → Glyph → Phase := fun x _ => decide (x = 0)
def codonTestA : Codon := (0, 0, 1)
def codonTestB : Codon := (0, 0, 0)

/-- Два корректных лифтинга дают разные фазы на одной и той же паре кодонов. -/
theorem lifts_differ :
    liftFirst omegaTest codonTestA codonTestB ≠
      liftLast omegaTest codonTestA codonTestB := by
  native_decide

/-- Кодон `(0,0,1)` не лежит в образе `embed`. -/
def offDiagonal : Codon := (0, 0, 1)

theorem offDiagonal_not_embedded : ∀ x : Glyph, embed x ≠ offDiagonal := by
  native_decide

/-- Две кодонные таблицы: константа и таблица с одним перевёрнутым значением
    на паре `(offDiagonal, (0,0,0))`. -/
def OmegaBase : Codon → Codon → Phase := fun _ _ => true

def OmegaFlip : Codon → Codon → Phase :=
  fun c d => if c = offDiagonal ∧ d = (0, 0, 0) then false else true

/-- На всех 16 глифовых парах таблицы неразличимы. -/
theorem same_on_glyph_pairs :
    ∀ x y : Glyph,
      OmegaBase (embed x) (embed y) = OmegaFlip (embed x) (embed y) := by
  native_decide

/-- Но на паре кодонов вне диагонали они различаются. -/
theorem differ_on_codon_pair :
    OmegaBase offDiagonal (0, 0, 0) ≠ OmegaFlip offDiagonal (0, 0, 0) := by
  native_decide

/-- **Основной результат:** глифовая таблица ω не определяет кодонную Ω.
    Следовательно, класс допустимых фазовых таблиц на Σ³ строго шире
    любого лифтинга с Σ, и «полная классификация» обязана фиксировать уровень. -/
theorem glyph_scope_does_not_determine_codon_scope :
    (∀ x y : Glyph,
      OmegaBase (embed x) (embed y) = OmegaFlip (embed x) (embed y)) ∧
    OmegaBase offDiagonal (0, 0, 0) ≠ OmegaFlip offDiagonal (0, 0, 0) :=
  ⟨same_on_glyph_pairs, differ_on_codon_pair⟩

/-- **QLP-01, главное:** две `PhaseTable` с одинаковой областью `codon`,
    одинаковой глифовой таблицей и **разными** кодонными таблицами.
    Значит, выбор `scope_of_wire` недостаточен: при `codon` нужна ещё
    политика лифтинга, которой в первоисточнике нет. -/
theorem codon_scope_undetermined :
    ∃ T₁ T₂ : PhaseTable,
      T₁.scope = WireScope.codon ∧ T₂.scope = WireScope.codon ∧
        T₁.glyphPhase = T₂.glyphPhase ∧
          T₁.codonPhase ≠ T₂.codonPhase := by
  refine ⟨codonFirst omegaTest, codonLast omegaTest, rfl, rfl, rfl, ?_⟩
  intro h
  have h' := congrFun (congrFun h codonTestA) codonTestB
  exact lifts_differ h'

/-- Глифовая область даёт 16 пар, кодонная — 4096. Это и есть цена выбора. -/
theorem pair_counts : (4 * 4 : Nat) = 16 ∧ (64 * 64 : Nat) = 4096 := by
  decide

/-- Политика лифтинга не выводится из глифовой таблицы: оба лифтинга
    согласованы с ней на диагонали, но различаются вне диагонали. -/
theorem lift_policy_not_determined :
    restrict (liftFirst omegaTest) = restrict (liftLast omegaTest) ∧
      liftFirst omegaTest ≠ liftLast omegaTest := by
  refine ⟨?_, ?_⟩
  · funext x y
    rw [restrict_liftFirst, restrict_liftLast]
  · intro h
    have h' := congrFun (congrFun h codonTestA) codonTestB
    exact lifts_differ h'

#print axioms restrict_liftFirst
#print axioms lifts_differ
#print axioms offDiagonal_not_embedded
#print axioms same_on_glyph_pairs
#print axioms glyph_scope_does_not_determine_codon_scope
#print axioms codon_scope_undetermined
#print axioms lift_policy_not_determined

end QCat.Scope
