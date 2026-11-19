import QCatBraidCore.Braided
import QCatBraidCore.PhaseNaturality
import Mathlib.Data.List.Basic
import Mathlib.Data.Fintype.Card
import Mathlib.Logic.Equiv.Fin.Basic

/-!
# Типизированный объектный слой (F2, F3 аудита Илори)

Аудит `QCAT_CLOSURE_007_ILORI_AUDIT` указал две границы:

* **F2.** Уровни объектов различны: `Q-Mathematics v3.0` — `Ob = ℕ₀`
  (длина цепочки), `PQT-QCat T0` — `Ob = Σ*` (свободные цветные слова),
  `BraidCore` — `Ob = Type`. Отождествлять их нельзя; нужен явный
  объектный слой и семантическая карта.
* **F3.** `replace x y : Glyph → Glyph` — **выбранная модель** типизированной
  стрелки `r_{y←x} : x → y`, а не её определение. Замена стрелки глобальной
  функцией без отдельного `model_of` недопустима.

Этот файл вводит:

1. объекты `ColoredWord := List Glyph` (свободные цветные слова, `Σ*`);
2. типизированные стрелки `Rewrite` с `dom = [x]`, `cod = [y]` — то есть
   `r_{y←x} : [x] ⟶ [y]`, и `Braid` с `dom = [x,y]`, `cod = [y,x]`;
3. **явный** `modelOf : Rewrite → (Glyph → Glyph)` — интерпретацию,
   а не отождествление, с тремя теоремами:
   * `modelOf_respects_typing` — модель уважает типизацию;
   * `modelOf_injective` — модель **верна** (ничего не теряет);
   * `modelOf_comp_not_eq` — модель **не** делает `r_{z←y} ∘ r_{y←x}`
     равным `r_{z←x}`, что согласуется с §2.2 источника (отношение
     не постулируется);
4. `objectMap : ColoredWord → BraidCore K` и сравнения
   `unitComparison`, `appendComparison`.

**Чего здесь НЕТ.** `objectMap` **не** оформлен как `MonoidalFunctor`:
сравнения — изоморфизмы, а не равенства, потому что `List.append` и `Sum`
различны дефиниционно (`(w ++ v).length = w.length + v.length` — теорема,
а не `rfl`). Это ровно тот разрыв, на который указывает F2; выдавать его
за строгую эквивалентность было бы подменой.
-/

open CategoryTheory
open CategoryTheory.MonoidalCategory

namespace QCat
namespace Typed

/-! ### Алфавит и объекты -/

/-- Алфавит глифов `Σ = {0,1,2,3}`. -/
abbrev Glyph : Type := Fin 4

/-- Объект типизированного слоя: свободное цветное слово над `Σ`
    (историческое `Ob = Σ*`). -/
abbrev ColoredWord : Type := List Glyph

/-! ### Типизированные стрелки -/

/-- `r_{y←x} : [x] ⟶ [y]` при `x ≠ y` (§2.2 источника).
    Это **стрелка между одноэлементными словами**, а не функция. -/
structure Rewrite where
  /-- Исходный цвет `x`. -/
  src : Glyph
  /-- Целевой цвет `y`. -/
  tgt : Glyph
  /-- `x ≠ y`. -/
  ne : src ≠ tgt

/-- Домен `r_{y←x}` — слово `[x]`. -/
def Rewrite.dom (r : Rewrite) : ColoredWord := [r.src]

/-- Кодомен `r_{y←x}` — слово `[y]`. -/
def Rewrite.cod (r : Rewrite) : ColoredWord := [r.tgt]

/-- `b_{x,y} : [x,y] ⟶ [y,x]` (§2.3 источника). -/
structure Braid where
  /-- Левый цвет. -/
  left : Glyph
  /-- Правый цвет. -/
  right : Glyph

/-- Домен `b_{x,y}` — слово `[x,y]`. -/
def Braid.dom (b : Braid) : ColoredWord := [b.left, b.right]

/-- Кодомен `b_{x,y}` — слово `[y,x]`. -/
def Braid.cod (b : Braid) : ColoredWord := [b.right, b.left]

/-! ### `model_of`: явная интерпретация, а не отождествление (F3) -/

/-- **Выбранная модель.** Типизированная стрелка `r_{y←x}` интерпретируется
    глобальной функцией «заменить `x` на `y`, остальное не трогать».

    Это `def`, а не `abbrev`-отождествление: обратное утверждение
    («стрелка ЕСТЬ эта функция») не доказывается и не предполагается. -/
def modelOf (r : Rewrite) : Glyph → Glyph := PhaseNaturality.replace r.src r.tgt

/-- Модель переводит `x` в `y`. -/
@[simp]
theorem modelOf_src (r : Rewrite) : modelOf r r.src = r.tgt :=
  PhaseNaturality.replace_self r.src r.tgt

/-- Модель не трогает остальные цвета. -/
theorem modelOf_of_ne (r : Rewrite) {a : Glyph} (h : a ≠ r.src) : modelOf r a = a :=
  PhaseNaturality.replace_of_ne h

/-- **Модель уважает типизацию:** образ домена поточечно равен кодомену. -/
theorem modelOf_respects_typing (r : Rewrite) :
    (r.dom.map (modelOf r)) = r.cod := by
  simp [Rewrite.dom, Rewrite.cod]

/-- **Модель верна (faithful):** разные типизированные стрелки дают разные
    глобальные функции. Значит переход к модели не склеивает генераторы
    и не теряет информацию о паре `(x, y)`. -/
theorem modelOf_injective : Function.Injective modelOf := by
  rintro ⟨x, y, hne⟩ ⟨x', y', hne'⟩ h
  have hxx : x = x' := by
    by_contra hc
    have h1 : modelOf ⟨x', y', hne'⟩ x = x := modelOf_of_ne _ hc
    have h2 : modelOf ⟨x, y, hne⟩ x = y := modelOf_src _
    have hyx : y = x := by rw [← h2, congrFun h x, h1]
    exact hne hyx.symm
  subst hxx
  have hyy : y = y' := by
    have h2 : modelOf ⟨x, y, hne⟩ x = y := modelOf_src _
    have h3 : modelOf ⟨x, y', hne'⟩ x = y' := modelOf_src _
    rw [← h2, congrFun h x, h3]
  subst hyy
  rfl

/-- **Модель согласуется с отсутствием отношения композиции.**
    В источнике (§2.2) не постулируется `r_{z←y} ∘ r_{y←x} = r_{z←x}`.
    Глобальная модель этому тоже не удовлетворяет: на цвете `y` левая
    часть даёт `y`, правая — `z`.

    Тем самым модель не «улучшает» источник и не добавляет лишних
    соотношений. -/
theorem modelOf_comp_not_eq (x y z : Glyph) (hxy : x ≠ y) (hyz : y ≠ z) (hxz : x ≠ z) :
    (modelOf ⟨x, z, hxz⟩ : Glyph → Glyph) ≠
      fun a => modelOf ⟨y, z, hyz⟩ (modelOf ⟨x, y, hxy⟩ a) := by
  intro h
  have key := congrFun h y
  simp only [modelOf, PhaseNaturality.replace, hxy.symm, if_false, if_true] at key
  exact hyz key

/-! ### Объектный слой: слова → `BraidCore` (F2) -/

variable {K : Type} [CommMonoid K]

/-- Объектная карта: слово длины `n` переходит в носитель `Fin n`.
    Пустое слово — в пустой носитель, то есть в единицу тензора. -/
def objectMap (w : ColoredWord) : BraidCore K := ⟨Fin w.length⟩

/-- Сравнение для единицы: `[]` даёт `Fin 0`, а `𝟙_` — `PEmpty`.
    Это **изоморфизм**, а не равенство. -/
def unitComparison : (objectMap ([] : ColoredWord) : BraidCore K).carrier ≃
    (𝟙_ (BraidCore K)).carrier :=
  Equiv.equivPEmpty (Fin 0)

/-- Сравнение для тензора: `w ++ v` даёт `Fin (|w| + |v|)`, а `⊗` — сумму
    носителей. Изоморфизм есть, равенства нет: `(w ++ v).length = |w| + |v|`
    — теорема `List.length_append`, а не `rfl`. Именно здесь проходит
    граница F2 между строгой словесной презентацией и `BraidCore`. -/
def appendComparison (w v : ColoredWord) :
    (objectMap (K := K) (w ++ v)).carrier ≃
      (tensorObj (objectMap (K := K) w) (objectMap (K := K) v)).carrier := by
  show Fin (w ++ v).length ≃ (Fin w.length ⊕ Fin v.length)
  rw [List.length_append]
  exact finSumFinEquiv.symm

omit [CommMonoid K] in
/-- Носитель объектной карты — ровно `Fin` длины слова (это `rfl`):
    объектный слой не «теряет» и не «добавляет» провода. -/
theorem objectMap_carrier (w : ColoredWord) :
    (objectMap (K := K) w).carrier = Fin w.length := rfl

end Typed
end QCat
