/-
  QCAT-CAT-BRIDGE-001 — корневой модуль
  =====================================

  Мост: QCat-008 → конечная стохастическая динамика → наблюдатель с
  first-return trace.

  Слои (контракт, п.0): символический QCat → **выбранное** стохастическое
  представление (не внутренне присущее) → V/H-наблюдатель → операциональные
  наблюдаемые.

  Модули:
  * `MarkovKernel`      — M1: `StochMatrix` над ℚ, замыкание, ядро `Q_w`,
                          фикстуры `Q4`/`QNU`, обструкция «фаза ≠ стохастика».
  * `ObserverTrace`     — M2: блоки, `Tr_V = A + B(I−D)⁻¹C` только при
                          сертифицированном обратном, неотрицательность,
                          суммы строк, ряд Неймана как тождество с остатком,
                          граница поглощающего класса, фикстуры `Q_RGB`/`Q4`.
  * `TraceComposition`  — M3: контрпример `Tr(P·R) ≠ Tr(P)·Tr(R)`,
                          yanking для чистого свопа.
  * `TowerLaw`          — M3: башня `Tr_{V2}(Tr_{V1}(Q)) = Tr_{V2}(Q)` с
                          тремя сертифицированными обратными (ADDENDUM-003,
                          исправленная формула `(I − M)⁻¹`).
  * `PhaseObservation`  — M4: `Π_λ`, критерий видимости, слепота `e₊`,
                          немультипликативность, выпуклые смеси, точный
                          дефект проекции (H1).
  * `SignRealization`   — H2: `M(g) = [[p_stay,p_flip],[p_flip,p_stay]]` как
                          неверная (nonfaithful) реализация `{±1}²`.
  * `Audit`             — `#print axioms` по критическим теоремам.
-/
import QCatCatBridge.MarkovKernel
import QCatCatBridge.ObserverTrace
import QCatCatBridge.TraceComposition
import QCatCatBridge.TowerLaw
import QCatCatBridge.PhaseObservation
import QCatCatBridge.SignRealization
import QCatCatBridge.Audit
