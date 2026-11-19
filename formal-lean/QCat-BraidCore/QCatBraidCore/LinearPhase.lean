import QCatBraidCore.ColoredWord
import Mathlib.Algebra.Module.LinearMap.Defs
import Mathlib.Algebra.Ring.Prod
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Group.Units.Defs

/-!
# Линейное представление фазового braiding (§4 аудита Илори)

Аудит `QCAT_CLOSURE_007_ILORI_AUDIT` §4 указал, что критерий из
`PhaseNaturality.lean` сформулирован для **глобальных функций** `A → A`,
а исторический генератор `r_{y←x}` — типизированная стрелка, действующая
на **линейном** представлении. В линейной картине сокращать множитель
нельзя: кольцо `Q₋₁` имеет делители нуля.

Этот файл строит линейную картину и доказывает обе натуральности
в виде произведений:

    u_yx · (ω(y,z) − ω(x,z)) = 0,        (левый провод)
    u_yx · (ω(z,y) − ω(z,x)) = 0.        (правый провод)

Здесь `u_yx` — коэффициент типизированной стрелки `r_{y←x}`,
`ω` — фаза цветной braid-компоненты. Оба входа — скаляры в
коммутативном кольце `R`; цвет представлен модулем `R`.

## Что доказывается

* `naturality_left_iff` / `naturality_right_iff` — **точные** критерии:
  равенство линейных карт ⇔ произведение равно нулю. Не «следует из»,
  а «равносильно».
* `all_units_imply_constant` — **условная** теорема: если все `u_yx`
  обратимы, то `ω` постоянна. Условие обратимости существенно.
* `zero_divisor_blocks_conclusion` — **свидетель** того, что при
  `u = e₊ ≠ 0` вывод не проходит: две различные обратимые фазы `1` и `ι`
  дают одинаковый результат. Это не «no-go», а демонстрация того, что
  безусловного no-go здесь нет.
* `distinct_phases_same_morphism` — тот же свидетель на уровне самих
  линейных карт.

## Чего здесь НЕТ

Никакого утверждения о T0 целиком: память `δ`, dagger, `Witness` не
затронуты. Свидетель — это **чистая фазово-переписывательная** часть;
его согласованность с dagger/memory не проверялась и не заявляется.
-/

namespace QCat
namespace LinearPhase

/-! ### Скалярное умножение как линейная карта -/

section Generic

variable {R : Type} [CommRing R]

/-- Умножение на скаляр `a` как `R`-линейная карта `R → R`. -/
def scal (a : R) : R →ₗ[R] R := a • LinearMap.id

@[simp]
theorem scal_apply (a r : R) : scal a r = a * r := by
  simp [scal]

/-- Композиция скалярных карт — умножение скаляров. -/
theorem scal_mul (a b : R) : (scal a).comp (scal b) = scal (a * b) := by
  ext
  simp [scal, mul_assoc]

/-- Скалярная карта однозначно определяет скаляр (действие на `1`). -/
theorem scal_injective : Function.Injective (scal (R := R)) := by
  intro a b h
  have := congrArg (fun f : R →ₗ[R] R => f 1) h
  simpa [scal] using this

/-- **Сокращение обратимого множителя.** В коммутативном кольце
    `a * b = 0` при обратимом `a` даёт `b = 0`. В `Q₋₁` это неверно
    для необратимого `a` — см. `zero_divisor_blocks_conclusion`. -/
theorem eq_zero_of_unit_mul {a b : R} (ha : IsUnit a) (h : a * b = 0) : b = 0 := by
  obtain ⟨v, hv⟩ := isUnit_iff_exists_inv.mp ha
  have hv' : v * a = 1 := by rw [mul_comm, hv]
  calc b = 1 * b := (one_mul b).symm
    _ = (v * a) * b := by rw [hv']
    _ = v * (a * b) := by rw [mul_assoc]
    _ = v * 0 := by rw [h]
    _ = 0 := mul_zero v

/-- **Натуральность по левому проводу — точный критерий.**

    Два пути: «переписать первый провод, затем сплести» и «сплести,
    затем переписать второй провод». Их равенство как линейных карт
    равносильно `u * (ω_yz − ω_xz) = 0`. -/
theorem naturality_left_iff (u ωyz ωxz : R) :
    (scal ωyz).comp (scal u) = (scal u).comp (scal ωxz) ↔ u * (ωyz - ωxz) = 0 := by
  rw [scal_mul, scal_mul, scal_injective.eq_iff]
  constructor
  · intro h
    have h' : u * ωyz = u * ωxz := by rw [mul_comm u ωyz]; exact h
    rw [mul_sub, sub_eq_zero]
    exact h'
  · intro h
    rw [mul_sub, sub_eq_zero] at h
    rw [mul_comm ωyz u]
    exact h

/-- **Натуральность по правому проводу — точный критерий:**
    `u * (ω_zy − ω_zx) = 0`. -/
theorem naturality_right_iff (u ωzy ωzx : R) :
    (scal ωzy).comp (scal u) = (scal u).comp (scal ωzx) ↔ u * (ωzy - ωzx) = 0 := by
  rw [scal_mul, scal_mul, scal_injective.eq_iff]
  constructor
  · intro h
    have h' : u * ωzy = u * ωzx := by rw [mul_comm u ωzy]; exact h
    rw [mul_sub, sub_eq_zero]
    exact h'
  · intro h
    rw [mul_sub, sub_eq_zero] at h
    rw [mul_comm ωzy u]
    exact h

end Generic

/-! ### Представление, индексированное цветами -/

variable {R : Type} [CommRing R]

/-- Цветная braid-компонента `b_{x,z}` в линейном представлении:
    умножение на `ω x z`. -/
def braidLin (ω : Typed.Glyph → Typed.Glyph → R) (x z : Typed.Glyph) : R →ₗ[R] R :=
  scal (ω x z)

/-- Типизированная стрелка `r_{y←x}` в линейном представлении:
    умножение на `u x y`. -/
def rewriteLin (u : Typed.Glyph → Typed.Glyph → R) (x y : Typed.Glyph) : R →ₗ[R] R :=
  scal (u x y)

/-- Натуральность по левому проводу, в форме произведения. -/
theorem naturality_left_iff_phases (ω u : Typed.Glyph → Typed.Glyph → R)
    (x y z : Typed.Glyph) :
    (braidLin ω y z).comp (rewriteLin u x y) =
        (rewriteLin u x y).comp (braidLin ω x z) ↔
      u x y * (ω y z - ω x z) = 0 :=
  naturality_left_iff (u x y) (ω y z) (ω x z)

/-- Натуральность по правому проводу, в форме произведения. -/
theorem naturality_right_iff_phases (ω u : Typed.Glyph → Typed.Glyph → R)
    (x y z : Typed.Glyph) :
    (braidLin ω z y).comp (rewriteLin u x y) =
        (rewriteLin u x y).comp (braidLin ω z x) ↔
      u x y * (ω z y - ω z x) = 0 :=
  naturality_right_iff (u x y) (ω z y) (ω z x)

/-- **Условная теорема (§4).** Если все коэффициенты `u_yx` (`x ≠ y`)
    обратимы, то фазовая таблица постоянна.

    Обратимость — не косметика: без неё утверждение ложно
    (`zero_divisor_blocks_conclusion`). -/
theorem all_units_imply_constant (ω u : Typed.Glyph → Typed.Glyph → R)
    (hu : ∀ x y, x ≠ y → IsUnit (u x y))
    (hL : ∀ x y z, x ≠ y → u x y * (ω y z - ω x z) = 0)
    (hR : ∀ x y z, x ≠ y → u x y * (ω z y - ω z x) = 0)
    (a a' b b' : Typed.Glyph) : ω a b = ω a' b' := by
  have h1 : ω a b = ω a' b := by
    by_cases ha : a = a'
    · rw [ha]
    · have hz : ω a' b - ω a b = 0 := eq_zero_of_unit_mul (hu a a' ha) (hL a a' b ha)
      exact (sub_eq_zero.mp hz).symm
  have h2 : ω a' b = ω a' b' := by
    by_cases hb : b = b'
    · rw [hb]
    · have hz : ω a' b' - ω a' b = 0 := eq_zero_of_unit_mul (hu b b' hb) (hR b b' a' hb)
      exact (sub_eq_zero.mp hz).symm
  rw [h1, h2]

/-! ### `Q₋₁` как `ℝ × ℝ`: делители нуля ломают безусловный вывод -/

/-- Расщеплённо-комплексное кольцо `Q₋₁ ≅ ℝ × ℝ` в координатах
    идемпотентов: `(a, b) = a·e₊ + b·e₋`. -/
abbrev SplitComplex : Type := ℝ × ℝ

/-- Идемпотент `e₊ = (1, 0)`. -/
def eplus : SplitComplex := (1, 0)

/-- Идемпотент `e₋ = (0, 1)`. -/
def eminus : SplitComplex := (0, 1)

/-- Мнимая единица `ι = e₊ − e₋`, `ι² = 1`. -/
def iota : SplitComplex := (1, -1)

theorem eplus_ne_zero : eplus ≠ (0 : SplitComplex) := by
  intro h
  have := congrArg Prod.fst h
  norm_num [eplus] at this

theorem eplus_mul_eminus : eplus * eminus = (0 : SplitComplex) := by
  ext <;> norm_num [eplus, eminus]

theorem iota_mul_self : iota * iota = (1 : SplitComplex) := by
  ext <;> norm_num [iota]

theorem iota_isUnit : IsUnit iota :=
  isUnit_iff_exists_inv.mpr ⟨iota, iota_mul_self⟩

theorem iota_ne_one : iota ≠ (1 : SplitComplex) := by
  intro h
  have h2 : (-1 : ℝ) = 1 := by simpa [iota] using congrArg Prod.snd h
  have h3 : (2 : ℝ) = 0 := by
    have h4 : (-1 : ℝ) + 1 = 1 + 1 := by rw [h2]
    simpa using h4.symm
  exact two_ne_zero h3

theorem eplus_mul_one_eq_eplus_mul_iota : eplus * (1 : SplitComplex) = eplus * iota := by
  ext <;> norm_num [eplus, iota]

/-- **Свидетель: безусловного no-go нет.**

    `u = e₊ ≠ 0`, обе фазы `1` и `ι` обратимы и различны, но
    `u · 1 = u · ι`. Значит из `u_yx ≠ 0` **нельзя** вывести
    `ω(y,z) = ω(x,z)` над кольцом с делителями нуля. -/
theorem zero_divisor_blocks_conclusion :
    ∃ (u ω₁ ω₂ : SplitComplex),
      u ≠ 0 ∧ IsUnit ω₁ ∧ IsUnit ω₂ ∧ ω₁ ≠ ω₂ ∧ u * ω₁ = u * ω₂ :=
  ⟨eplus, 1, iota, eplus_ne_zero, isUnit_one, iota_isUnit, Ne.symm iota_ne_one,
    eplus_mul_one_eq_eplus_mul_iota⟩

/-- Тот же свидетель на уровне линейных карт: две **различные** обратимые
    фазы дают **один и тот же** морфизм после умножения на `e₊`. -/
theorem distinct_phases_same_morphism :
    (scal (1 : SplitComplex)).comp (scal eplus) =
      (scal eplus).comp (scal iota) := by
  rw [naturality_left_iff, mul_sub, sub_eq_zero]
  exact eplus_mul_one_eq_eplus_mul_iota

end LinearPhase
end QCat
