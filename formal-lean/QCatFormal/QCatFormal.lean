-- QCatFormal: машинно проверяемое ядро QCat.
-- Lean 4.18.0 + Mathlib v4.18.0 (офлайн-снимок ../mathlib-v4.18.0), версии зафиксированы совместно.
--
-- Порядок импортов соответствует уточнённому плану (2026-11-07) и итерации QLP-01..06:
-- сначала первоисточник QMath_v3.md, затем независимые модели и их сравнение.
import QCatFormal.Basic          -- фиксация связки версий Lean 4.18.0 + Mathlib v4.18.0
import QCatFormal.StdOnly        -- независимый слой: только ядро Lean + Std, диэдральная R
import QCatFormal.Scope          -- QLP-01: scope_of_wire (glyph|codon) и лифтинг ω 4→64
import QCatFormal.Comparison     -- QLP-03: NaturalRewrite, braid_label_actions_differ
import QCatFormal.Historical     -- ПЕРВОИСТОЧНИК: σᵢ(a,b) = ω(a,b)·(b,a), YBE(B2) и симметричность
import QCatFormal.BraidRelations -- B1 (частный σ₁/σ₃) и обратимость σᵢ при Q₋₁ˣ-фазах
import QCatFormal.GeneralBraid   -- B1 и B2 для всех длин n и всех позиций
import QCatFormal.FreeModule     -- QLP-02: K-линейный σ на Triple →₀ K, перенос YBE по линейности
import QCatFormal.QAlgebra       -- этап 1: Q₋₁, идемпотенты e±
import QCatFormal.Qm1NBad        -- QLP-04: Q₋₁-native контрмодель N-bad (единицы 1 и −1)
import QCatFormal.RMap           -- этап 2: диэдральная R на ZMod 64 (альтернативная модель)
import QCatFormal.Naturality     -- этап 3 / QLP-05: скалярная контрмодель, not_claimed(N1,T0)
import QCatFormal.MathlibBridge  -- этап 6: доступность BraidedCategory / hexagon в Mathlib
import QCatFormal.Audit          -- этап 6: аудит аксиом (#print axioms)
