/-
  QCAT-CAT-BRIDGE-001 · АУДИТ АКСИОМ
  ==================================

  Требование контракта (п.6): `#print axioms` по критическим теоремам,
  `sorryAx = 0`, отсутствие `sorry`/`admit`/`unsafe`/пользовательских аксиом.

  Ожидаемый допустимый набор: `propext`, `Classical.choice`, `Quot.sound`.
  Появление `sorryAx` или любого пользовательского имени — провал приёмки.
-/
import QCatCatBridge.MarkovKernel
import QCatCatBridge.ObserverTrace
import QCatCatBridge.TraceComposition
import QCatCatBridge.PhaseObservation
import QCatCatBridge.SignRealization
import QCatCatBridge.TowerLaw

/-! ### M1: стохастические матрицы и обструкция -/

#print axioms QCat.Bridge.StochMatrix.mul_apply
#print axioms QCat.Bridge.StochMatrix.one_apply
#print axioms QCat.Bridge.StochMatrix.mul_assoc_toMatrix
#print axioms QCat.Bridge.StochMatrix.ofWeights
#print axioms QCat.Bridge.StochMatrix.Q4_row_sums
#print axioms QCat.Bridge.StochMatrix.QNU_row_sums
#print axioms QCat.Bridge.StochMatrix.QNU_not_symmetric
#print axioms QCat.Bridge.card_offdiag_glyph
#print axioms QCat.Bridge.StochMatrix.swapMatrix_row_sum
#print axioms QCat.Bridge.StochMatrix.stochastic_phase_forces_one
#print axioms QCat.Bridge.StochMatrix.nontrivial_phase_not_stochastic

/-! ### M2: след первого возвращения -/

#print axioms QCat.Bridge.row_split_V
#print axioms QCat.Bridge.row_split_H
#print axioms QCat.Bridge.rowsum_C_eq
#print axioms QCat.Bridge.traceV_nonneg
#print axioms QCat.Bridge.inner_row_sum
#print axioms QCat.Bridge.traceV_row_sum
#print axioms QCat.Bridge.inv1_mul
#print axioms QCat.Bridge.traceV1_nonneg
#print axioms QCat.Bridge.traceV1_row_sum
#print axioms QCat.Bridge.geom_mul
#print axioms QCat.Bridge.geom_partial
#print axioms QCat.Bridge.geom_terminates
#print axioms QCat.Bridge.absorbing_no_inverse
#print axioms QCat.Bridge.absorbing_gives_substochastic
#print axioms QCat.Bridge.QRGB_invertible
#print axioms QCat.Bridge.QRGB_trace
#print axioms QCat.Bridge.QRGB_trace_row_sums
#print axioms QCat.Bridge.Q4T_invertible
#print axioms QCat.Bridge.Q4T_trace
#print axioms QCat.Bridge.Q4T_kac_ratio

/-! ### M3: композиция и её границы -/

#print axioms QCat.Bridge.Pmat_row_sum
#print axioms QCat.Bridge.Rmat_row_sum
#print axioms QCat.Bridge.P_invertible
#print axioms QCat.Bridge.R_invertible
#print axioms QCat.Bridge.TrP_values
#print axioms QCat.Bridge.TrR_values
#print axioms QCat.Bridge.TrPR_values
#print axioms QCat.Bridge.trace_not_functorial
#print axioms QCat.Bridge.swapBlock_blockA
#print axioms QCat.Bridge.swapBlock_blockB
#print axioms QCat.Bridge.swapBlock_blockC
#print axioms QCat.Bridge.swapBlock_blockD
#print axioms QCat.Bridge.yanking

/-! ### M4: фаза и наблюдение -/

#print axioms QCat.Bridge.iota_sq
#print axioms QCat.Bridge.eplus_mul_eminus
#print axioms QCat.Bridge.zero_divisors
#print axioms QCat.Bridge.iota_not_cone
#print axioms QCat.Bridge.visibility_iff
#print axioms QCat.Bridge.eplus_blind
#print axioms QCat.Bridge.eplus_blind_criterion
#print axioms QCat.Bridge.lossy_cannot_recover
#print axioms QCat.Bridge.Pi_not_multiplicative
#print axioms QCat.Bridge.Pi_half_witness
#print axioms QCat.Bridge.convex_mix_nonneg
#print axioms QCat.Bridge.convex_mix_sum
#print axioms QCat.Bridge.convex_mix_stochastic

/-! ### H1: точный дефект проекции (ADDENDUM-002) -/

#print axioms QCat.Bridge.Pi_defect
#print axioms QCat.Bridge.Pi_multiplicative_iff
#print axioms QCat.Bridge.Pi_defect_eplus_eminus
#print axioms QCat.Bridge.mulSC_injective_iff

/-! ### H2: знаковая реализация (ADDENDUM-002) -/

#print axioms QCat.Bridge.sgn_sq
#print axioms QCat.Bridge.pStay_add_pFlip
#print axioms QCat.Bridge.pFlip_add_pStay
#print axioms QCat.Bridge.sgn_add_eq_zero_of_ne
#print axioms QCat.Bridge.pStay_eq_one_of_eq
#print axioms QCat.Bridge.pFlip_eq_zero_of_eq
#print axioms QCat.Bridge.pStay_eq_zero_of_ne
#print axioms QCat.Bridge.pFlip_eq_one_of_ne
#print axioms QCat.Bridge.Mmat_iff
#print axioms QCat.Bridge.Mmat_row_sum
#print axioms QCat.Bridge.Mmat_perm
#print axioms QCat.Bridge.Mmat_nonneg
#print axioms QCat.Bridge.Mmat_gPlus
#print axioms QCat.Bridge.Mmat_gMixed
#print axioms QCat.Bridge.Mmat_gNegAll
#print axioms QCat.Bridge.Mstoch_gPlus
#print axioms QCat.Bridge.add_fst_eq_snd_iff
#print axioms QCat.Bridge.Mswap_mul_self
#print axioms QCat.Bridge.Mmat_mul
#print axioms QCat.Bridge.Mstoch_mul
#print axioms QCat.Bridge.Mmat_kernel_at_one
#print axioms QCat.Bridge.Mmat_global_sign_blind
#print axioms QCat.Bridge.Mmat_not_injective
#print axioms QCat.Bridge.sign_realization_summary

/-! ## ADDENDUM-003 — Tower Law (исправленная формула) -/
#print axioms QCat.Bridge.rowBlock_mul_fromBlocks
#print axioms QCat.Bridge.mulColBlock
#print axioms QCat.Bridge.rowBlock_mul_colBlock
#print axioms QCat.Bridge.schurInv_mul
#print axioms QCat.Bridge.tower_schur
#print axioms QCat.Bridge.traceV_eq_traceMat
#print axioms QCat.Bridge.mBlockA_traceV
#print axioms QCat.Bridge.mBlockB_traceV
#print axioms QCat.Bridge.mBlockC_traceV
#print axioms QCat.Bridge.tower_traceV
#print axioms QCat.Bridge.c_hD
#print axioms QCat.Bridge.c_hS
#print axioms QCat.Bridge.c_hT
#print axioms QCat.Bridge.c_tower_value
#print axioms QCat.Bridge.c_tower
#print axioms QCat.Bridge.c_wrong_value
