-- SQL-аналитика по платежам симулятора цифрового рубля.
-- Запросы написаны под PostgreSQL (БД из docker-compose).

-- 1. Распределение платежей по статусам
SELECT
    status,
    COUNT(*)                                        AS payments_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_percent
FROM payments
GROUP BY status
ORDER BY payments_count DESC;

-- 2. Конверсия платежей в успешные (по завершённым платежам)
SELECT
    COUNT(*) FILTER (WHERE status = 'PAID')                       AS paid_count,
    COUNT(*) FILTER (WHERE status IN ('PAID', 'FAILED'))          AS finished_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'PAID')
        / NULLIF(COUNT(*) FILTER (WHERE status IN ('PAID', 'FAILED')), 0),
        2
    )                                                             AS conversion_percent
FROM payments;

-- 3. Среднее время обработки платежа (от создания до финального статуса)
SELECT
    status,
    ROUND(AVG(EXTRACT(EPOCH FROM (updated_at - created_at)))::numeric, 2)
        AS avg_processing_seconds
FROM payments
WHERE status IN ('PAID', 'FAILED')
GROUP BY status;

-- 4. Динамика платежей по дням: количество и оборот успешных
SELECT
    DATE(created_at)                                   AS day,
    COUNT(*)                                           AS payments_count,
    COALESCE(SUM(amount) FILTER (WHERE status = 'PAID'), 0) AS paid_turnover
FROM payments
GROUP BY DATE(created_at)
ORDER BY day;

-- 5. Топ пользователей по сумме успешных платежей
SELECT
    u.email,
    COUNT(p.id)      AS paid_payments,
    SUM(p.amount)    AS total_paid
FROM payments p
JOIN users u ON u.id = p.user_id
WHERE p.status = 'PAID'
GROUP BY u.email
ORDER BY total_paid DESC
LIMIT 10;

-- 6. Средний чек успешного платежа
SELECT
    ROUND(AVG(amount), 2) AS avg_payment_amount,
    MIN(amount)           AS min_payment_amount,
    MAX(amount)           AS max_payment_amount
FROM payments
WHERE status = 'PAID';

-- 7. Сверка: баланс кошелька против суммы транзакций
-- (проверка целостности данных — значения должны совпадать)
SELECT
    w.id                                   AS wallet_id,
    u.email,
    w.balance                              AS wallet_balance,
    COALESCE(SUM(
        CASE WHEN t.type = 'DEPOSIT' THEN t.amount ELSE -t.amount END
    ), 0)                                  AS transactions_sum
FROM wallets w
JOIN users u ON u.id = w.user_id
LEFT JOIN transactions t ON t.wallet_id = w.id
GROUP BY w.id, u.email, w.balance
ORDER BY w.id;
