import Mathlib.CategoryTheory.Monoidal.Braided.Basic

/-!
# Стыковка с категорийной инфраструктурой Mathlib (этап 6, проверка доступности)

Илори отдельно потребовала использовать готовую инфраструктуру Mathlib:
`BraidedCategory`, естественность брейдинга, тождества гексагона.
Ниже `#check` подтверждает, что в **зафиксированной** связке
Lean 4.18.0 + Mathlib v4.18.0 эти декларации существуют под ожидаемыми
именами; дополнительно проверена готовая категорийная теорема
`BraidedCategory.yang_baxter` (Mathlib/.../Braided/Basic.lean:147).

**Факт версии.** В v4.18.0 объединённая естественность называется
`CategoryTheory.BraidedCategory.braiding_naturality`, а НЕ
`CategoryTheory.braiding_naturality`. Первое имя фиксируется сборкой,
второе отсутствует.

**Граница заявленного (`not_claimed`).** Здесь проверена только доступность
деклараций. Мы НЕ строим экземпляр `BraidedCategory QCat` и НЕ переносим
доказательства из `Historical.lean` / `RMap.lean` в категорийную форму:
это следующий этап, требующий задания `Category`, `MonoidalCategory` и
`braiding` для QCat с проверкой `hexagon_forward` / `hexagon_reverse`.
Попытка выдать `#check` за доказательство была бы ровно той ошибкой,
которую Lean призван предотвратить.
-/

#check CategoryTheory.BraidedCategory
#check CategoryTheory.BraidedCategory.braiding
#check CategoryTheory.BraidedCategory.braiding_naturality_left
#check CategoryTheory.BraidedCategory.braiding_naturality_right
-- В Mathlib v4.18.0 объединённая естественность лежит ВНУТРИ неймспейса
-- `BraidedCategory`, а не в корне `CategoryTheory`: имя
-- `CategoryTheory.braiding_naturality` отсутствует (проверено сборкой,
-- QCatFormal.MathlibBridge:25). Это зафиксировано как факт версии.
#check CategoryTheory.BraidedCategory.braiding_naturality
#check CategoryTheory.BraidedCategory.hexagon_forward
#check CategoryTheory.BraidedCategory.hexagon_reverse
#check CategoryTheory.BraidedCategory.yang_baxter
#check CategoryTheory.MonoidalCategory
