/-
# `QCatBraidCore` — конструктивное брайд-ядро QCat

QCAT-CATEGORY-CLOSURE-007, п.3–6.

Проект строит **конструктивно** (без `axiom`, без `sorry`) ровно тот
структурный скелет, который в историческом QCat задан формулами

    σᵢ(xᵢ, xᵢ₊₁) = ω(xᵢ, xᵢ₊₁) · (xᵢ₊₁, xᵢ),      ω(x, y) ∈ Q₋₁ˣ,

а именно:

* `Basic`           — категория `BraidCore K`: объект = носитель меток,
                      морфизм = «фаза + биекция»; `Category` доказана.
* `Monoidal`        — `⊗` = `⊕` носителей, `𝟙_` = пустой носитель;
                      `MonoidalCategory` доказана (пентагон, треугольник,
                      естественность ассоциатора и юниторов).
* `Braided`         — `β_ X Y` = `Equiv.sumComm` с единичной фазой;
                      `BraidedCategory` доказана (обе естественности,
                      оба шестиугольника).
* `PhaseNaturality` — критерий естественности **фазового** множителя
                      `ω` относительно унарных переписываний (п.4)
                      и теорема «все унарные ⇒ `ω` постоянна» (п.5).
* `Generators`      — реестр 12 генераторов `r_{y←x}` и 16 компонентов
                      `b_{x,y}` из первичного текста (п.6), плюс шаблон
                      требования многоместной naturality.

Итерация 008 (по аудиту Илори `QCAT_CLOSURE_007_ILORI_AUDIT`):

* `Braided.braiding_double_eq_id` + `instSymmetricCategory` — F1:
  симметричность стала утверждением в типе класса, а не в комментарии.
* `ColoredWord`     — F2/F3: объектный слой `Σ*`, типизированные стрелки
                      `r_{y←x} : [x] ⟶ [y]`, `b_{x,y} : [x,y] ⟶ [y,x]`
                      и **явный** `modelOf` в глобальные функции с
                      доказательством верности модели.
* `LinearPhase`     — §4: линейное представление, обе натуральности в виде
                      `u·(ω₁−ω₂)=0`, условная теорема при обратимости `u`
                      и свидетель над `Q₋₁ = ℝ × ℝ`, показывающий, что
                      безусловного no-go нет.
* `Braided`/`Basic` — F4: `BraidCore Kˣ` как точная фазовая модель.

**Чего проект НЕ утверждает:** полной QCat, памяти `δ`, `T`, `μ_δ`,
`Witness`, `QCat₂L`, физических следствий. Соответствие исходным формулам
с точностью до строк — в `README.md`.
-/
import QCatBraidCore.Basic
import QCatBraidCore.Monoidal
import QCatBraidCore.Braided
import QCatBraidCore.PhaseNaturality
import QCatBraidCore.ColoredWord
import QCatBraidCore.LinearPhase
import QCatBraidCore.Generators
