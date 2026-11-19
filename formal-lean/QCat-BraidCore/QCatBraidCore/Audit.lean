import QCatBraidCore

/-!
# Аудит аксиом (QCAT-CATEGORY-CLOSURE-007, критерий приёмки)

Каждая строка `#print axioms` печатает множество аксиом, от которых
зависит константа. Ожидаемый результат для всего файла:

* ни одна константа не зависит от `sorryAx`;
* ни одна константа не зависит от пользовательских `axiom`;
* допустимый остаток — только стандартные аксиомы Lean/Mathlib:
  `propext`, `Classical.choice`, `Quot.sound` и `Lean.ofReduceBool`
  (последняя — от тактики `decide` в `Generators.lean`).

Аудит включает **сами экземпляры** `Category`, `MonoidalCategory`,
`BraidedCategory`: если бы какая-то когерентность была постулирована,
она всплыла бы здесь.
-/

namespace QCat

/-! ### Категория (`Basic.lean`) -/

#print axioms BraidCore.instCategory
#print axioms BraidCore.Hom.ext
#print axioms BraidCore.isoOfEquiv

/-! ### Моноидальная структура (`Monoidal.lean`) -/

#print axioms BraidCore.instMonoidalCategory
#print axioms BraidCore.instIsEmptyTensorUnitCarrier
#print axioms BraidCore.tensorObj_carrier
#print axioms BraidCore.tensorUnit_carrier
#print axioms BraidCore.whiskerLeft_phase
#print axioms BraidCore.whiskerRight_phase
#print axioms BraidCore.associator_hom_phase
#print axioms BraidCore.associator_inv_phase

/-! ### Сплетение (`Braided.lean`) -/

#print axioms BraidCore.instBraidedCategory
#print axioms BraidCore.braiding_phase
#print axioms BraidCore.braiding_perm
#print axioms BraidCore.braiding_apply_inl
#print axioms BraidCore.braiding_apply_inr
#print axioms BraidCore.braiding_perm_comp_self

/-! ### Фазовая естественность (`PhaseNaturality.lean`, п.4–5) -/

#print axioms PhaseNaturality.sigma_natural_left_iff
#print axioms PhaseNaturality.sigma_natural_right_iff
#print axioms PhaseNaturality.constant_phase_natural
#print axioms PhaseNaturality.phaseNaturalLeft_of_left_indep
#print axioms PhaseNaturality.all_unary_implies_constant
#print axioms PhaseNaturality.constants_imply_constant
#print axioms PhaseNaturality.replace_natural_left_iff
#print axioms PhaseNaturality.replace_natural_right_iff
#print axioms PhaseNaturality.generators_imply_constant

/-! ### Реестр генераторов (`Generators.lean`, п.6) -/

#print axioms Generators.card_glyph
#print axioms Generators.card_rewriteGenerators
#print axioms Generators.card_rewriteGen
#print axioms Generators.card_braidingComponents
#print axioms Generators.card_braidingGen
#print axioms Generators.rewriteGenFun_src
#print axioms Generators.rewriteGenFun_of_ne
#print axioms Generators.braidingGenSwap_involutive
#print axioms Generators.multiPlace_two_left_iff
#print axioms Generators.multiPlace_two_right_iff

/-! ### F1 / F4: симметричность и точная фазовая модель -/

#print axioms BraidCore.braiding_double_eq_id
#print axioms BraidCore.instSymmetricCategory
#print axioms BraidCore.phase_isUnit
#print axioms BraidCore.isIso_of_isUnit_phase

/-! ### F2 / F3: типизированный объектный слой (`ColoredWord.lean`) -/

#print axioms Typed.modelOf_respects_typing
#print axioms Typed.modelOf_injective
#print axioms Typed.modelOf_comp_not_eq
#print axioms Typed.unitComparison
#print axioms Typed.appendComparison
#print axioms Typed.objectMap_carrier

/-! ### §4: линейное представление (`LinearPhase.lean`) -/

#print axioms LinearPhase.scal_mul
#print axioms LinearPhase.scal_injective
#print axioms LinearPhase.eq_zero_of_unit_mul
#print axioms LinearPhase.naturality_left_iff
#print axioms LinearPhase.naturality_right_iff
#print axioms LinearPhase.naturality_left_iff_phases
#print axioms LinearPhase.naturality_right_iff_phases
#print axioms LinearPhase.all_units_imply_constant
#print axioms LinearPhase.eplus_ne_zero
#print axioms LinearPhase.iota_isUnit
#print axioms LinearPhase.zero_divisor_blocks_conclusion
#print axioms LinearPhase.distinct_phases_same_morphism

end QCat
