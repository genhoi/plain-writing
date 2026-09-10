## Что сделано

Ветка `feature/refund-discount-fix` по задаче SHOP-517, обсуждение в треде. После спайка по `RefundCalculator` стало понятно, что старая логика не ретраится нормально, поэтому сделал минимальный аккуратный фикс.

- `RefundCalculator.php`: переписан метод `calculate()`, добавлен `applyDiscountShare()`.
- `RefundService.php`: вызов нового метода, убран старый бэкофф.
- `RefundCalculatorTest.php`: тесты.
- `config/refund.php`: новый флаг `refund.proportional`.

Изменение fail-closed: если пропорцию посчитать нельзя, возврат не создаётся. Честно говоря, старый код было проще выкинуть.

## Не вошло

Пересчёт бонусов и возвраты по заказам из ветки `legacy-orders`. Сделаем в SHOP-520.
