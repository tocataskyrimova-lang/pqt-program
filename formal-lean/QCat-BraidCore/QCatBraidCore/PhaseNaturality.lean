import Mathlib.Algebra.Group.Basic

/-!
# Критерий естественности фазового сплетения (QCAT-CATEGORY-CLOSURE-007, п.4–5)

Историческое сплетение QCat:

    σ(a, b) = ω(a, b) · (b, a),      ω(a, b) ∈ Q₋₁ˣ.

Оно состоит из **перестановки** `(a,b) ↦ (b,a)` и **скаляра** `ω(a,b)`.
В `Braided.lean` перестановочная часть оформлена как настоящая
braided-структура. Здесь рассматривается вопрос, который перестановка
не решает: когда *фазовый множитель* ведёт себя естественно относительно
переписываний?

## Что доказывается

Пусть `f : A → A` — унарное переписывание (в историческом QCat это
`r_{y←x}`, применённое к одному проводу).

* `sigma_natural_left_iff` — **точный** критерий: квадрат

      σ(f a, b)  =  (ω(f a, b), (b, f a))
      (ω(a,b), (b,a)) после переписывания второго провода

  коммутирует тогда и только тогда, когда `ω(f a, b) = ω(a, b)`.
  То есть «естественность фазового сплетения по левому аргументу»
  **эквивалентна** требованию п.4 задания — не сильнее и не слабее.

* `sigma_natural_right_iff` — то же для `ω(a, f b) = ω(a, b)`.

* `all_unary_implies_constant` (п.5) — если допустимы **все** унарные
  функции, фазовая таблица постоянна.

* `generators_imply_constant` — усиление: достаточно не «всех функций»,
  а только исторических генераторов `r_{y←x}` при `x ≠ y` (то есть
  12 переписываний на 4 глифах). Более того, достаточно даже **констант**
  `fun _ => a'` (`constants_imply_constant`).

## Чего здесь НЕТ

Никаких утверждений о `Q₋₁`, о памяти `δ`, о `Witness`, о `QCat₂L`.
`K` — произвольный тип; **обратимость `ω` не используется** (как и в
доказательстве YBE: скалярное тождество её не требует). Это отдельный
факт, а не следствие структуры `Q₋₁`.
-/

namespace QCat
namespace PhaseNaturality

variable {K : Type} {A : Type}

/-! ### Одно сплетение как функция на парах -/

/-- Сплетение с фазой: `(a, b) ↦ (ω a b, (b, a))`. -/
def sigma (ω : A → A → K) (p : A × A) : K × (A × A) := (ω p.1 p.2, (p.2, p.1))

/-- Переписывание `f` на **первом** проводе пары. -/
def rewriteLeft (f : A → A) (p : A × A) : A × A := (f p.1, p.2)

/-- Переписывание `f` на **втором** проводе пары. -/
def rewriteRight (f : A → A) (p : A × A) : A × A := (p.1, f p.2)

/-- **Критерий естественности по левому аргументу.**

Квадрат
```
        σ
(a, b) ─────▶ (ω a b, (b, a))
   │                      │
 f │                      │ f на втором проводе
   ▼                      ▼
(f a, b) ───▶ (ω (f a) b, (b, f a))
        σ
```
коммутирует тогда и только тогда, когда `ω (f a) b = ω a b`.

Формально: `sigma ω (f a, b)` совпадает со «сплетением, а затем
переписыванием второго провода» ровно при этом условии. -/
theorem sigma_natural_left_iff (ω : A → A → K) (f : A → A) (a b : A) :
    sigma ω (f a, b) = ((sigma ω (a, b)).1, rewriteRight f (sigma ω (a, b)).2) ↔
      ω (f a) b = ω a b := by
  constructor
  · intro h
    exact congrArg Prod.fst h
  · intro h
    simp only [sigma, rewriteRight, h]

/-- **Критерий естественности по правому аргументу:** `ω a (f b) = ω a b`. -/
theorem sigma_natural_right_iff (ω : A → A → K) (f : A → A) (a b : A) :
    sigma ω (a, f b) = ((sigma ω (a, b)).1, rewriteLeft f (sigma ω (a, b)).2) ↔
      ω a (f b) = ω a b := by
  constructor
  · intro h
    exact congrArg Prod.fst h
  · intro h
    simp only [sigma, rewriteLeft, h]

/-! ### Определения «фазовой естественности» (п.4) -/

/-- Требование п.4 задания, левая половина: `ω (f a) b = ω a b` для всех `a, b`. -/
def PhaseNaturalLeft (ω : A → A → K) (f : A → A) : Prop :=
  ∀ a b, ω (f a) b = ω a b

/-- Требование п.4 задания, правая половина: `ω a (f b) = ω a b` для всех `a, b`. -/
def PhaseNaturalRight (ω : A → A → K) (f : A → A) : Prop :=
  ∀ a b, ω a (f b) = ω a b

/-- Постоянная фазовая таблица. -/
def IsConstant (ω : A → A → K) : Prop :=
  ∀ a a' b b', ω a b = ω a' b'

/-! ### Постоянная таблица естественна (обратная сторона критерия) -/

/-- Постоянная таблица естественна по любому переписыванию. -/
theorem constant_phase_natural (ω : A → A → K) (h : IsConstant ω) (f : A → A) :
    PhaseNaturalLeft ω f ∧ PhaseNaturalRight ω f :=
  ⟨fun a b => h (f a) a b b, fun a b => h a a (f b) b⟩

/-- Если `ω` не зависит от первого аргумента, то `PhaseNaturalLeft` выполнено
    для любой `f`. -/
theorem phaseNaturalLeft_of_left_indep (ω : A → A → K)
    (h : ∀ a a' b, ω a b = ω a' b) (f : A → A) : PhaseNaturalLeft ω f :=
  fun a b => h (f a) a b

/-! ### п.5: все унарные функции допустимы ⇒ таблица постоянна -/

/-- **п.5 задания.** Если фазовая таблица естественна по **всем** унарным
    функциям (с обеих сторон), то она постоянна.

    Доказательство не требует ничего, кроме двух константных функций:
    `fun _ => a'` даёт `ω a' b = ω a b`, а `fun _ => b'` даёт
    `ω a' b' = ω a' b`. -/
theorem all_unary_implies_constant (ω : A → A → K)
    (hL : ∀ f : A → A, PhaseNaturalLeft ω f)
    (hR : ∀ f : A → A, PhaseNaturalRight ω f) : IsConstant ω := by
  intro a a' b b'
  have h1 : ω a' b = ω a b := hL (fun _ => a') a b
  have h2 : ω a' b' = ω a' b := hR (fun _ => b') a' b
  rw [← h1, ← h2]

/-- **Усиление п.5.** Достаточно, чтобы были допустимы одни лишь
    **константные** функции `fun _ => c`; «все унарные функции» не нужны. -/
theorem constants_imply_constant (ω : A → A → K)
    (hL : ∀ c : A, PhaseNaturalLeft ω (fun _ => c))
    (hR : ∀ c : A, PhaseNaturalRight ω (fun _ => c)) : IsConstant ω := by
  intro a a' b b'
  have h1 : ω a' b = ω a b := hL a' a b
  have h2 : ω a' b' = ω a' b := hR b' a' b
  rw [← h1, ← h2]

/-! ### Исторические генераторы `r_{y←x}` -/

/-- Переписывание «заменить `x` на `y`»: `x ↦ y`, остальные глифы на месте. -/
def replace [DecidableEq A] (x y : A) : A → A := fun a => if a = x then y else a

/-- Действие `r_{y←x}` на самом `x` даёт `y`. -/
@[simp]
theorem replace_self [DecidableEq A] (x y : A) : replace x y x = y := by
  simp [replace]

/-- Действие `r_{y←x}` вне `x` — тождественно. -/
@[simp]
theorem replace_of_ne [DecidableEq A] {x y a : A} (h : a ≠ x) : replace x y a = a := by
  simp [replace, h]

/-- **Ключевой шаг.** Если `r_{y←x}` (`x ≠ y`) допустимо слева,
    то столбец `b ↦ ω · b` не различает `x` и `y`. -/
theorem replace_natural_left_iff [DecidableEq A] (ω : A → A → K) {x y : A} (hxy : x ≠ y) :
    PhaseNaturalLeft ω (replace x y) ↔ ∀ b, ω y b = ω x b := by
  constructor
  · intro h b
    have := h x b
    simpa using this
  · intro h a b
    by_cases ha : a = x
    · subst ha
      simpa using h b
    · simp [replace, ha]

/-- Аналогично справа. -/
theorem replace_natural_right_iff [DecidableEq A] (ω : A → A → K) {x y : A} (hxy : x ≠ y) :
    PhaseNaturalRight ω (replace x y) ↔ ∀ a, ω a y = ω a x := by
  constructor
  · intro h a
    have := h a x
    simpa using this
  · intro h a b
    by_cases hb : b = x
    · subst hb
      simpa using h a
    · simp [replace, hb]

/-- **п.5 в исторической форме.** Если допустимы все генераторы
    `r_{y←x}` при `x ≠ y` (12 штук на четырёх глифах), то фазовая
    таблица постоянна.

    Это строго сильнее, чем «нужны все унарные функции»: достаточно
    двенадцати переписываний.

    **Граница (F3 аудита Илори).** Теорема говорит о **глобальных заменах**
    `Glyph → Glyph`, а не о типизированных стрелках `r_{y←x} : [x] ⟶ [y]`
    bare T0. Перенос на типизированный уровень — не автоматический:
    там множитель `u_yx` может быть необратимым, и вывод слабеет до
    `u_yx · (ω₁ − ω₂) = 0`. См. `LinearPhase.all_units_imply_constant`
    (условная теорема) и `LinearPhase.zero_divisor_blocks_conclusion`
    (почему условие существенно). -/
theorem generators_imply_constant [DecidableEq A] (ω : A → A → K)
    (hL : ∀ x y : A, x ≠ y → PhaseNaturalLeft ω (replace x y))
    (hR : ∀ x y : A, x ≠ y → PhaseNaturalRight ω (replace x y)) : IsConstant ω := by
  intro a a' b b'
  have step1 : ω a b = ω a' b := by
    by_cases ha : a = a'
    · rw [ha]
    · exact ((replace_natural_left_iff ω ha).mp (hL a a' ha) b).symm
  have step2 : ω a' b = ω a' b' := by
    by_cases hb : b = b'
    · rw [hb]
    · exact ((replace_natural_right_iff ω hb).mp (hR b b' hb) a').symm
  rw [step1, step2]

end PhaseNaturality
end QCat
