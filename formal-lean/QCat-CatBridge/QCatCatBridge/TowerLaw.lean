/-
  QCAT-CAT-BRIDGE-001 · ADDENDUM-003 — TOWER LAW
  ===============================================

  `Tr_{V2}(Tr_{V1}(Q)) = Tr_{V2}(Q)` при `V2 ⊆ V1`, с точными guards.

  ИСПРАВЛЕНИЕ ФОРМУЛЫ (аудит Илори 2026-11-08).
  В `CORRESPONDENCE.md` §M3 ранее стояло `[[A22,B2],[C2,D]]⁻¹` — **без** `I −`.
  Верно: `(I − [[A22,B2],[C2,D]])⁻¹`. На контрольной матрице
  `Q = [[1/4,1/2,1/4],[1/3,1/3,1/3],[1/2,0,1/2]]` ошибочная формула даёт `1/2`,
  верная — `1`. Здесь формализована **верная**; ошибочная не переносилась.

  СОДЕРЖАНИЕ
  * `tower_schur`  — точное тождество «Schur complement of Schur complement»
    с тремя сертификатами: `Dinv`, `Sinv`, `Tinv`.
  * `tower_traceV` — то же на уровне `traceV`: двойной след равен одношаговому.
  * `c_*`          — полная машинная проверка контрольной точки аддендума,
    включая `tower_schur` на её числах.

  ЧЕГО ЗДЕСЬ НЕТ
  * Traced-моноидальная структура (JSV) не заявляется: доказано одно
    тождество для одного разбиения, а не аксиомы traced-структуры.
  * Никаких утверждений о неотрицательности/стохастичности в `tower_schur`:
    это чистая линейная алгебра над `ℚ`. Вероятностные guards остаются
    в `ObserverTrace.lean` (`traceV_nonneg`, `traceV_row_sum`).
-/
import QCatCatBridge.TraceComposition
import Mathlib.Data.Matrix.Block
import Mathlib.Tactic.Abel

open scoped BigOperators

namespace QCat
namespace Bridge

/-! ## 0. Локальная тактика для матричных тождеств

`noncomm_ring` на `Matrix` нормализует `-x` в `-1 • x`, после чего `-1 • x`
и `x` становятся разными атомами и тождество не закрывается. Поэтому:
сначала дистрибутивность + ассоциативность (`simp only`), затем `abel`.
Это чисто линейная алгебра над `ℚ` — никаких вероятностных предпосылок. -/

macro "mat_ring" : tactic =>
  `(tactic| (simp only [Matrix.mul_add, Matrix.mul_sub, Matrix.add_mul, Matrix.sub_mul,
      Matrix.mul_neg, Matrix.neg_mul, Matrix.mul_assoc,
      Matrix.mul_one, Matrix.one_mul]; abel))

/-! ## 1. Блочная строка `[X, Y]` и блочный столбец `[X; Y]`

`Matrix.fromBlocks` работает только с квадратной разбивкой (`n ⊕ o` на
`l ⊕ m`). Для прямоугольных блоков вводятся отдельные обёртки: именно они
встречаются в `Tr_{V2}(Q) = A11 + [A12, B1] · K · [A21; C1]`. -/

/-- Блочная строка `[X, Y] : Matrix a (b ⊕ c)`. -/
def rowBlock {a b c : Type*} (X : Matrix a b ℚ) (Y : Matrix a c ℚ) : Matrix a (b ⊕ c) ℚ :=
  fun i k => Sum.elim (fun j => X i j) (fun j => Y i j) k

/-- Блочный столбец `[X; Y] : Matrix (b ⊕ c) a`. -/
def colBlock {a b c : Type*} (X : Matrix b a ℚ) (Y : Matrix c a ℚ) : Matrix (b ⊕ c) a ℚ :=
  fun k j => Sum.elim (fun i => X i j) (fun i => Y i j) k

@[simp] theorem rowBlock_inl {a b c : Type*} (X : Matrix a b ℚ) (Y : Matrix a c ℚ)
    (i : a) (j : b) : rowBlock X Y i (Sum.inl j) = X i j := rfl

@[simp] theorem rowBlock_inr {a b c : Type*} (X : Matrix a b ℚ) (Y : Matrix a c ℚ)
    (i : a) (j : c) : rowBlock X Y i (Sum.inr j) = Y i j := rfl

@[simp] theorem colBlock_inl {a b c : Type*} (X : Matrix b a ℚ) (Y : Matrix c a ℚ)
    (i : b) (j : a) : colBlock X Y (Sum.inl i) j = X i j := rfl

@[simp] theorem colBlock_inr {a b c : Type*} (X : Matrix b a ℚ) (Y : Matrix c a ℚ)
    (i : c) (j : a) : colBlock X Y (Sum.inr i) j = Y i j := rfl

/-! ## 2. Прямоугольные законы умножения

Это `Matrix.fromBlocks_multiply` для случаев «одна блочная строка» и «один блочный
столбец» — ровно то, что нужно для угла `[A12,B1] · K · [A21;C1]`. -/

theorem rowBlock_mul_fromBlocks {a b c d e : Type*}
    [Fintype b] [Fintype c]
    (X : Matrix a b ℚ) (Y : Matrix a c ℚ)
    (P : Matrix b d ℚ) (Q : Matrix b e ℚ) (R : Matrix c d ℚ) (S : Matrix c e ℚ) :
    rowBlock X Y * Matrix.fromBlocks P Q R S = rowBlock (X * P + Y * R) (X * Q + Y * S) := by
  ext i j
  rcases j with j | j <;>
    simp [rowBlock, Matrix.fromBlocks, Matrix.mul_apply, Matrix.add_apply,
      Fintype.sum_sum_type, Finset.sum_add_distrib]

theorem mulColBlock {a b c d e : Type*}
    [Fintype d] [Fintype e]
    (P : Matrix b d ℚ) (Q : Matrix b e ℚ) (R : Matrix c d ℚ) (S : Matrix c e ℚ)
    (X : Matrix d a ℚ) (Y : Matrix e a ℚ) :
    Matrix.fromBlocks P Q R S * colBlock X Y = colBlock (P * X + Q * Y) (R * X + S * Y) := by
  ext i j
  rcases i with i | i <;>
    simp [colBlock, Matrix.fromBlocks, Matrix.mul_apply, Matrix.add_apply,
      Fintype.sum_sum_type, Finset.sum_add_distrib]

theorem rowBlock_mul_colBlock {a b c : Type*} [Fintype b] [Fintype c]
    (X : Matrix a b ℚ) (Y : Matrix a c ℚ) (U : Matrix b a ℚ) (V : Matrix c a ℚ) :
    rowBlock X Y * colBlock U V = X * U + Y * V := by
  ext i j
  simp [rowBlock, colBlock, Matrix.mul_apply, Matrix.add_apply,
    Fintype.sum_sum_type, Finset.sum_add_distrib]

/-! ## 3. Кандидат в обратный к `I − [[A22,B2],[C2,D]]`

`Sinv` — сертифицированный обратный к `1 − S22`, где `S22 = A22 + B2·Dinv·C2`.
Тогда обратный к `1 − M` выписывается явно через блочную формулу Шура по
второму блоку (элиминируем `D` первым — именно этот `Dinv` у нас и есть). -/

/-- Явный кандидат: `(1 − [[A22,B2],[C2,D]])⁻¹`
`= [[Σ⁻¹, Σ⁻¹ B2 D⁻¹],[D⁻¹ C2 Σ⁻¹, D⁻¹ + D⁻¹ C2 Σ⁻¹ B2 D⁻¹]]`, `Σ = 1 − S22`. -/
def schurInv {b c : Type*} [Fintype b] [Fintype c]
    (Dinv : Matrix c c ℚ) (Sinv : Matrix b b ℚ)
    (B2 : Matrix b c ℚ) (C2 : Matrix c b ℚ) : Matrix (b ⊕ c) (b ⊕ c) ℚ :=
  Matrix.fromBlocks Sinv (Sinv * B2 * Dinv) (Dinv * C2 * Sinv)
    (Dinv + Dinv * C2 * Sinv * B2 * Dinv)

/-- `schurInv` действительно левый обратный к `1 − Matrix.fromBlocks A22 B2 C2 D`.

    Guards: `Dinv * (1 − D) = 1` и `Sinv * (1 − S22) = 1`.
    Нужны именно **левые** обратные в этой форме; правая сторона здесь
    не используется. -/
theorem schurInv_mul {b c : Type*} [Fintype b] [Fintype c]
    [DecidableEq b] [DecidableEq c]
    (A22 : Matrix b b ℚ) (B2 : Matrix b c ℚ) (C2 : Matrix c b ℚ) (D : Matrix c c ℚ)
    (Dinv : Matrix c c ℚ) (Sinv : Matrix b b ℚ)
    (hD : Dinv * (1 - D) = 1)
    (hS : Sinv * (1 - (A22 + B2 * Dinv * C2)) = 1) :
    schurInv Dinv Sinv B2 C2 * (1 - Matrix.fromBlocks A22 B2 C2 D) = 1 := by
  have hN : (1 : Matrix (b ⊕ c) (b ⊕ c) ℚ) - Matrix.fromBlocks A22 B2 C2 D
      = Matrix.fromBlocks (1 - A22) (-B2) (-C2) (1 - D) := by
    rw [sub_eq_add_neg, Matrix.fromBlocks_neg, ← Matrix.fromBlocks_one, Matrix.fromBlocks_add]
    simp [sub_eq_add_neg]
  -- `Sinv · (1 − A22) = 1 + Sinv B2 Dinv C2` — разворачиваем guard `hS`.
  have hS1 : Sinv * (1 - A22) = 1 + Sinv * B2 * Dinv * C2 := by
    have h : Sinv * (1 - (A22 + B2 * Dinv * C2))
        = Sinv * (1 - A22) - Sinv * B2 * Dinv * C2 := by
      mat_ring
    rw [h] at hS
    exact sub_eq_iff_eq_add.mp hS
  have hone : (1 : Matrix (b ⊕ c) (b ⊕ c) ℚ) = Matrix.fromBlocks 1 0 0 1 :=
    Matrix.fromBlocks_one.symm
  rw [hN, hone, schurInv, Matrix.fromBlocks_multiply, Matrix.fromBlocks_inj]
  refine ⟨?_, ?_, ?_, ?_⟩
  · -- (1,1): `Sinv (1−A22) − Sinv B2 Dinv C2 = Sinv (1 − S22) = 1`
    have h1 : Sinv * (1 - A22) + (Sinv * B2 * Dinv) * (-C2)
        = Sinv * (1 - (A22 + B2 * Dinv * C2)) := by
      mat_ring
    rw [h1, hS]
  · -- (1,2): `−Sinv B2 + Sinv B2 (Dinv (1−D)) = 0`
    have h2 : Sinv * (-B2) + (Sinv * B2 * Dinv) * (1 - D) = 0 := by
      have e : Sinv * (-B2) + (Sinv * B2 * Dinv) * (1 - D)
          = Sinv * B2 * (Dinv * (1 - D) - 1) := by
        mat_ring
      rw [e, hD]
      simp
    exact h2
  · -- (2,1): `Dinv C2 (Sinv (1−A22)) − Dinv C2 − Dinv C2 Sinv B2 Dinv C2 = 0`
    have e1 : (Dinv * C2 * Sinv) * (1 - A22) = Dinv * C2 * (Sinv * (1 - A22)) := by
      simp only [Matrix.mul_assoc]
    rw [e1, hS1]
    mat_ring
  · -- (2,2): `−Dinv C2 Sinv B2 + Dinv (1−D) + Dinv C2 Sinv B2 (Dinv (1−D)) = 1`
    have e : (Dinv * C2 * Sinv) * (-B2) + (Dinv + Dinv * C2 * Sinv * B2 * Dinv) * (1 - D)
        = Dinv * (1 - D) + Dinv * C2 * Sinv * B2 * (Dinv * (1 - D))
          - Dinv * C2 * Sinv * B2 := by
      mat_ring
    rw [e, hD]
    simp

/-! ## 4. TOWER LAW — точное тождество

Разбиение `(a) ⊕ (b) ⊕ (c)`: `a = V2`, `b = V1 \ V2`, `c = H`.

* `Tr_{V1}(Q)` — след по `c`; его блоки суть `A11 + B1 Dinv C1` и т.д.;
* `Tr_{V2}(Tr_{V1}(Q))` — след по `b` от результата;
* `Tr_{V2}(Q)` — след по `b ⊕ c` сразу, с `(I − [[A22,B2],[C2,D]])⁻¹`.

Тождество утверждает, что оба порядка дают одно и то же. -/

/-- **TOWER LAW (Schur complement of Schur complement).**

    Guards — три явных сертификата:
    * `hD : Dinv * (1 − D) = 1` — обратный к `I − D`;
    * `hS : Sinv * (1 − S22) = 1`, `S22 = A22 + B2 Dinv C2` — обратный к `I − S22`;
    * `hT : (1 − M) * Tinv = 1`, `M = [[A22,B2],[C2,D]]` — обратный к `I − M`
      (правая сторона; левая выводится из `schurInv_mul`).

    Заключение:
    `A11 + [A12,B1] Tinv [A21;C1]
       = A11 + B1 Dinv C1 + (A12 + B1 Dinv C2) Sinv (A21 + B2 Dinv C1)`. -/
theorem tower_schur {a b c : Type*} [Fintype a] [Fintype b] [Fintype c]
    [DecidableEq a] [DecidableEq b] [DecidableEq c]
    (A11 : Matrix a a ℚ) (A12 : Matrix a b ℚ) (B1 : Matrix a c ℚ)
    (A21 : Matrix b a ℚ) (A22 : Matrix b b ℚ) (B2 : Matrix b c ℚ)
    (C1 : Matrix c a ℚ) (C2 : Matrix c b ℚ) (D : Matrix c c ℚ)
    (Dinv : Matrix c c ℚ) (hD : Dinv * (1 - D) = 1)
    (Sinv : Matrix b b ℚ) (hS : Sinv * (1 - (A22 + B2 * Dinv * C2)) = 1)
    (Tinv : Matrix (b ⊕ c) (b ⊕ c) ℚ)
    (hT : (1 - Matrix.fromBlocks A22 B2 C2 D) * Tinv = 1) :
    A11 + rowBlock A12 B1 * Tinv * colBlock A21 C1
      = A11 + B1 * Dinv * C1 + (A12 + B1 * Dinv * C2) * Sinv * (A21 + B2 * Dinv * C1) := by
  have hleft : schurInv Dinv Sinv B2 C2 * (1 - Matrix.fromBlocks A22 B2 C2 D) = 1 :=
    schurInv_mul A22 B2 C2 D Dinv Sinv hD hS
  have hTinv : Tinv = schurInv Dinv Sinv B2 C2 := by
    calc Tinv = 1 * Tinv := (one_mul _).symm
      _ = (schurInv Dinv Sinv B2 C2 * (1 - Matrix.fromBlocks A22 B2 C2 D)) * Tinv := by rw [hleft]
      _ = schurInv Dinv Sinv B2 C2 * ((1 - Matrix.fromBlocks A22 B2 C2 D) * Tinv) := by rw [mul_assoc]
      _ = schurInv Dinv Sinv B2 C2 * 1 := by rw [hT]
      _ = schurInv Dinv Sinv B2 C2 := mul_one _
  rw [hTinv, schurInv, rowBlock_mul_fromBlocks, rowBlock_mul_colBlock]
  mat_ring

/-! ## 5. Уровень `traceV`: двойной след равен одношаговому

`traceV` определён только для `StochMatrix`. Чтобы применить его дважды,
вводится матричный (не вероятностный) вариант той же формулы и блочные
экстракторы без требований стохастичности. -/

/-- Блок `V → V` матрицы на `V ⊕ H` (без требований стохастичности). -/
def mBlockA {V H : Type*} (M : Matrix (V ⊕ H) (V ⊕ H) ℚ) : Matrix V V ℚ :=
  fun i j => M (Sum.inl i) (Sum.inl j)

/-- Блок `V → H`. -/
def mBlockB {V H : Type*} (M : Matrix (V ⊕ H) (V ⊕ H) ℚ) : Matrix V H ℚ :=
  fun i k => M (Sum.inl i) (Sum.inr k)

/-- Блок `H → V`. -/
def mBlockC {V H : Type*} (M : Matrix (V ⊕ H) (V ⊕ H) ℚ) : Matrix H V ℚ :=
  fun k j => M (Sum.inr k) (Sum.inl j)

/-- Блок `H → H`. -/
def mBlockD {V H : Type*} (M : Matrix (V ⊕ H) (V ⊕ H) ℚ) : Matrix H H ℚ :=
  fun k l => M (Sum.inr k) (Sum.inr l)

/-- Матричный след: `A + B · Dinv · C`. Та же формула, что `traceV`,
но без упаковки в `StochMatrix`. -/
def traceMat {V H : Type*} [Fintype V] [Fintype H]
    (M : Matrix (V ⊕ H) (V ⊕ H) ℚ) (Dinv : Matrix H H ℚ) :
    Matrix V V ℚ :=
  mBlockA M + mBlockB M * Dinv * mBlockC M

/-- `traceV` — это `traceMat` на носителе. -/
theorem traceV_eq_traceMat {V H : Type*} [Fintype V] [DecidableEq V]
    [Fintype H] [DecidableEq H] (Q : StochMatrix (V ⊕ H)) (Dinv : Matrix H H ℚ) :
    traceV Q Dinv = traceMat Q.toMatrix Dinv := rfl

/-- Блоки `Q` по тройному разбиению `(V2 ⊕ W) ⊕ H`: угол `V2 → V2`. -/
def tA11 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix V2 V2 ℚ :=
  fun i j => Q (Sum.inl (Sum.inl i)) (Sum.inl (Sum.inl j))

/-- `V2 → W`. -/
def tA12 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix V2 W ℚ :=
  fun i j => Q (Sum.inl (Sum.inl i)) (Sum.inl (Sum.inr j))

/-- `V2 → H`. -/
def tB1 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix V2 H ℚ :=
  fun i h => Q (Sum.inl (Sum.inl i)) (Sum.inr h)

/-- `W → V2`. -/
def tA21 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix W V2 ℚ :=
  fun k j => Q (Sum.inl (Sum.inr k)) (Sum.inl (Sum.inl j))

/-- `W → W`. -/
def tA22 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix W W ℚ :=
  fun k l => Q (Sum.inl (Sum.inr k)) (Sum.inl (Sum.inr l))

/-- `W → H`. -/
def tB2 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix W H ℚ :=
  fun k h => Q (Sum.inl (Sum.inr k)) (Sum.inr h)

/-- `H → V2`. -/
def tC1 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix H V2 ℚ :=
  fun h j => Q (Sum.inr h) (Sum.inl (Sum.inl j))

/-- `H → W`. -/
def tC2 {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix H W ℚ :=
  fun h k => Q (Sum.inr h) (Sum.inl (Sum.inr k))

/-- `H → H`. -/
def tD {V2 W H : Type*} (Q : Matrix ((V2 ⊕ W) ⊕ H) ((V2 ⊕ W) ⊕ H) ℚ) : Matrix H H ℚ :=
  fun h h' => Q (Sum.inr h) (Sum.inr h')

/-! Блоки `Tr_{V1}(Q)` (след по `H`) в терминах тройного разбиения. -/

theorem mBlockA_traceV {V2 W H : Type*} [Fintype V2] [DecidableEq V2]
    [Fintype W] [DecidableEq W] [Fintype H] [DecidableEq H]
    (Q : StochMatrix ((V2 ⊕ W) ⊕ H)) (Dinv : Matrix H H ℚ) :
    mBlockA (traceV Q Dinv) = tA11 Q.toMatrix + tB1 Q.toMatrix * Dinv * tC1 Q.toMatrix := by
  ext i j
  simp [traceV, mBlockA, mBlockB, mBlockC, tA11, tB1, tC1, blockA, blockB, blockC,
    Matrix.mul_apply, Matrix.add_apply]

theorem mBlockB_traceV {V2 W H : Type*} [Fintype V2] [DecidableEq V2]
    [Fintype W] [DecidableEq W] [Fintype H] [DecidableEq H]
    (Q : StochMatrix ((V2 ⊕ W) ⊕ H)) (Dinv : Matrix H H ℚ) :
    mBlockB (traceV Q Dinv) = tA12 Q.toMatrix + tB1 Q.toMatrix * Dinv * tC2 Q.toMatrix := by
  ext i j
  simp [traceV, mBlockB, mBlockA, mBlockC, tA12, tB1, tC2, blockA, blockB, blockC,
    Matrix.mul_apply, Matrix.add_apply]

theorem mBlockC_traceV {V2 W H : Type*} [Fintype V2] [DecidableEq V2]
    [Fintype W] [DecidableEq W] [Fintype H] [DecidableEq H]
    (Q : StochMatrix ((V2 ⊕ W) ⊕ H)) (Dinv : Matrix H H ℚ) :
    mBlockC (traceV Q Dinv) = tA21 Q.toMatrix + tB2 Q.toMatrix * Dinv * tC1 Q.toMatrix := by
  ext i j
  simp [traceV, mBlockC, mBlockA, mBlockB, tA21, tB2, tC1, blockA, blockB, blockC,
    Matrix.mul_apply, Matrix.add_apply]

/-- **TOWER LAW на уровне `traceV`.**

    `Tr_{V2}(Tr_{V1}(Q)) = Tr_{V2}(Q)`, где `V1 = V2 ⊕ W`.

    Слева — `traceMat` по `W` от `traceV` по `H`; справа — один след по `W ⊕ H`.
    Guards: `Dinv * (1 − D) = 1`, `Sinv * (1 − S22) = 1`,
    `(1 − M) * Tinv = 1`. -/
theorem tower_traceV {V2 W H : Type*} [Fintype V2] [DecidableEq V2]
    [Fintype W] [DecidableEq W] [Fintype H] [DecidableEq H]
    (Q : StochMatrix ((V2 ⊕ W) ⊕ H))
    (Dinv : Matrix H H ℚ) (hD : Dinv * oneMinusD Q = 1)
    (Sinv : Matrix W W ℚ)
    (hS : Sinv * (1 - (tA22 Q.toMatrix + tB2 Q.toMatrix * Dinv * tC2 Q.toMatrix)) = 1)
    (Tinv : Matrix (W ⊕ H) (W ⊕ H) ℚ)
    (hT : (1 - Matrix.fromBlocks (tA22 Q.toMatrix) (tB2 Q.toMatrix) (tC2 Q.toMatrix)
      (tD Q.toMatrix)) * Tinv = 1) :
    traceMat (traceV Q Dinv) Sinv
      = tA11 Q.toMatrix
        + rowBlock (tA12 Q.toMatrix) (tB1 Q.toMatrix) * Tinv
          * colBlock (tA21 Q.toMatrix) (tC1 Q.toMatrix) := by
  have hD' : Dinv * (1 - tD Q.toMatrix) = 1 := by
    have hEq : (1 - tD Q.toMatrix) = oneMinusD Q := by
      ext k l
      simp [oneMinusD, blockD, tD, Matrix.sub_apply, Matrix.one_apply]
    rw [hEq, hD]
  have h := tower_schur (tA11 Q.toMatrix) (tA12 Q.toMatrix) (tB1 Q.toMatrix)
    (tA21 Q.toMatrix) (tA22 Q.toMatrix) (tB2 Q.toMatrix)
    (tC1 Q.toMatrix) (tC2 Q.toMatrix) (tD Q.toMatrix) Dinv hD' Sinv hS Tinv hT
  rw [traceMat, mBlockA_traceV, mBlockB_traceV, mBlockC_traceV, ← h]

/-! ## 6. Контрольная точка аддендума — полная машинная проверка

`Q = [[1/4,1/2,1/4],[1/3,1/3,1/3],[1/2,0,1/2]]`, `V2={0}`, `V1={0,1}`, `H={2}`.
Все блоки одномерны, поэтому блоки — это скаляры (`Matrix (Fin 1) (Fin 1) ℚ`). -/

section Control

/-- `Q 0 0 = 1/4`. -/
def cA11 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 4
/-- `Q 0 1 = 1/2`. -/
def cA12 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 2
/-- `Q 0 2 = 1/4`. -/
def cB1 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 4
/-- `Q 1 0 = 1/3`. -/
def cA21 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 3
/-- `Q 1 1 = 1/3`. -/
def cA22 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 3
/-- `Q 1 2 = 1/3`. -/
def cB2 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 3
/-- `Q 2 0 = 1/2`. -/
def cC1 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 2
/-- `Q 2 1 = 0`. -/
def cC2 : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 0
/-- `Q 2 2 = 1/2`. -/
def cD : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 1 / 2

/-- `Dinv = (1 − 1/2)⁻¹ = 2`. -/
def cDinv : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 2

/-- `Sinv = (1 − 1/3)⁻¹ = 3/2`. -/
def cSinv : Matrix (Fin 1) (Fin 1) ℚ := fun _ _ => 3 / 2

/-- `Tinv = (I − [[1/3,1/3],[0,1/2]])⁻¹ = [[3/2,1],[0,2]]`. -/
def cTinv : Matrix (Fin 1 ⊕ Fin 1) (Fin 1 ⊕ Fin 1) ℚ :=
  Matrix.fromBlocks (fun _ _ => (3 : ℚ) / 2) (fun _ _ => 1) (fun _ _ => 0) (fun _ _ => 2)

theorem c_hD : cDinv * (1 - cD) = 1 := by
  ext i j
  fin_cases i
  fin_cases j
  simp [cDinv, cD, Matrix.mul_apply, Fin.sum_univ_one, Matrix.one_apply]
  norm_num

theorem c_hS : cSinv * (1 - (cA22 + cB2 * cDinv * cC2)) = 1 := by
  ext i j
  fin_cases i
  fin_cases j
  simp [cSinv, cA22, cB2, cDinv, cC2, Matrix.mul_apply, Fin.sum_univ_one, Matrix.one_apply]
  norm_num

theorem c_hT : (1 - Matrix.fromBlocks cA22 cB2 cC2 cD) * cTinv = 1 := by
  ext i j
  rcases i with i | i <;> rcases j with j | j <;>
    fin_cases i <;> fin_cases j <;>
    simp [cTinv, cA22, cB2, cC2, cD, Matrix.fromBlocks, Matrix.mul_apply, Fintype.sum_sum_type,
      Fin.sum_univ_one, Matrix.one_apply] <;>
    norm_num

/-- Значение «башни» (след по `H`, затем по `W`): `1`. -/
theorem c_tower_value :
    (cA11 + cB1 * cDinv * cC1
      + (cA12 + cB1 * cDinv * cC2) * cSinv * (cA21 + cB2 * cDinv * cC1))
      (0 : Fin 1) 0 = 1 := by
  simp [cA11, cA12, cB1, cA21, cA22, cB2, cC1, cC2, cDinv, cSinv,
    Matrix.mul_apply, Fin.sum_univ_one, Matrix.add_apply]
  norm_num

/-- **Tower Law на контрольной матрице:** `Tr_{V2}(Q) = 1`.

    Доказательство: `tower_schur` сводит левую часть к выражению «башни»,
    которое затем считается точно. -/
theorem c_tower :
    (cA11 + rowBlock cA12 cB1 * cTinv * colBlock cA21 cC1) (0 : Fin 1) 0 = 1 := by
  rw [tower_schur cA11 cA12 cB1 cA21 cA22 cB2 cC1 cC2 cD cDinv c_hD cSinv c_hS cTinv c_hT]
  exact c_tower_value

/-! ### Ошибочная формула (без `I −`) — почему её нельзя переносить в Lean

`M⁻¹ = [[3,−2],[0,2]]` вместо `(I − M)⁻¹ = [[3/2,1],[0,2]]`, итог `1/2 ≠ 1`.
Это арифметическая справка, а не теорема о следе. -/

/-- Ошибочное значение: `1/2`. -/
theorem c_wrong_value :
    (1 / 4 : ℚ) + ((1 / 2 : ℚ) * 3 + (1 / 4 : ℚ) * 0) * (1 / 3)
      + ((1 / 2 : ℚ) * (-2) + (1 / 4 : ℚ) * 2) * (1 / 2) = 1 / 2 := by
  norm_num

end Control

end Bridge
end QCat
