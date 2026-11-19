import QCatFormal.QAlgebra
import QCatFormal.Qm1NBad
import QCatFormal.RMap
import QCatFormal.Naturality
import QCatFormal.Historical
import QCatFormal.BraidRelations
import QCatFormal.GeneralBraid
import QCatFormal.FreeModule

/-!
# Аудит аксиом (этап 6 + итерация QLP)

`#print axioms` печатает при сборке список аксиом, от которых зависит
каждое доказательство. Ожидаемый набор — только стандартные аксиомы ядра
Lean/Mathlib (`propext`, `Classical.choice`, `Quot.sound`, `Lean.ofReduceBool`);
пользовательских аксиом и `sorry` быть не должно. Отдельно проверяется
отсутствие `sorryAx`: он появляется в выводе, если хоть одно доказательство
осталось незакрытым.
-/

-- Этап 1: Q₋₁, идемпотенты.
#print axioms QCat.QAlgebra.iota_sq
#print axioms QCat.QAlgebra.idempotents_classified
#print axioms QCat.QAlgebra.no_sqrt_neg_one
#print axioms QCat.QAlgebra.four_idempotents

-- QLP-04: Q₋₁-native контрмодель N-bad (без √−1, только единицы 1 и −1).
#print axioms QCat.Qm1NBad.omegaQ_invertible
#print axioms QCat.Qm1NBad.omegaQ_YBE
#print axioms QCat.Qm1NBad.omegaQ_monodromy
#print axioms QCat.Qm1NBad.omegaQ_not_scalar_flip
#print axioms QCat.Qm1NBad.nonzero_image_breaks_Qm1NBad
#print axioms QCat.Qm1NBad.Qm1_native_counterexample

-- Этап 2: диэдральная R (альтернативная модель).
#print axioms QCat.RMap.R_Rinv
#print axioms QCat.RMap.yang_baxter
#print axioms QCat.RMap.Rpow_formula
#print axioms QCat.RMap.Rpow_64
#print axioms QCat.RMap.not_involutive

-- Этап 3 / QLP-05: скалярная контрмодель (не модель T₀, не N1).
#print axioms QCat.Naturality.omegaNBad_monodromy
#print axioms QCat.Naturality.omegaNBad_not_scalar_flip
#print axioms QCat.Naturality.nonzero_image_breaks_NBad
#print axioms QCat.Naturality.scalar_zero_image_counterexample

-- Исторический QCat: фазово-перестановочный брейдинг.
#print axioms QCat.Historical.yang_baxter
#print axioms QCat.Historical.symmetric_iff_unit_monodromy
#print axioms QCat.Historical.nonsymmetric_without_relabelling
#print axioms QCat.Historical.constant_phase_symmetric_iff

-- B1 (частный случай σ₁/σ₃) и обратимость фазово-перестановочного брейдинга.
#print axioms QCat.BraidRelations.local_commutativity_B1
#print axioms QCat.BraidRelations.sigma12Inv_sigma12
#print axioms QCat.BraidRelations.sigma12_sigma12Inv

-- B1 и B2 для всех длин n и всех позиций.
#print axioms QCat.GeneralBraid.local_commutativity_general
#print axioms QCat.GeneralBraid.yang_baxter_general
#print axioms QCat.GeneralBraid.sigma1_sigma3

-- QLP-02: K-линейный σ на свободном модуле Triple →₀ K.
#print axioms QCat.FreeModule.sigma12Lin_single
#print axioms QCat.FreeModule.yang_baxter_single
#print axioms QCat.FreeModule.yang_baxter
#print axioms QCat.FreeModule.sigma12Lin_add
#print axioms QCat.FreeModule.sigma12Lin_smul
