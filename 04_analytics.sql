WITH status_counts AS (
    SELECT status, COUNT(*) AS payments_count
    FROM payments
    GROUP BY status
)
SELECT
    status,
    payments_count,
    ROUND(100.0 * payments_count / SUM(payments_count) OVER (), 2) AS percent
FROM status_counts
ORDER BY payments_count DESC;


SELECT
    COUNT(CASE WHEN status = 'PAID' THEN 1 END) AS paid,
    COUNT(*) AS finished,
    ROUND(100.0 * COUNT(CASE WHEN status = 'PAID' THEN 1 END) / COUNT(*), 2) AS conversion_percent
FROM payments
WHERE status IN ('PAID', 'FAILED');


SELECT
    status,
    ROUND(AVG(EXTRACT(EPOCH FROM updated_at - created_at)), 2) AS avg_seconds
FROM payments
WHERE status IN ('PAID', 'FAILED')
GROUP BY status;


WITH daily AS (
    SELECT
        created_at::DATE AS day,
        COUNT(*) AS payments_count,
        SUM(CASE WHEN status = 'PAID' THEN amount ELSE 0 END) AS paid_sum
    FROM payments
    GROUP BY created_at::DATE
)
SELECT
    day,
    payments_count,
    paid_sum,
    SUM(paid_sum) OVER (ORDER BY day) AS paid_sum_total
FROM daily
ORDER BY day;


SELECT
    ROUND(AVG(amount), 2) AS avg_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount
FROM payments
WHERE status = 'PAID';


SELECT
    u.email,
    COUNT(*) AS paid_payments,
    SUM(p.amount) AS total_paid
FROM payments p
JOIN users u ON u.id = p.user_id
WHERE p.status = 'PAID'
GROUP BY u.email
ORDER BY total_paid DESC
LIMIT 10;


WITH wallet_totals AS (
    SELECT
        wallet_id,
        SUM(CASE WHEN type = 'DEPOSIT' THEN amount ELSE -amount END) AS total
    FROM transactions
    GROUP BY wallet_id
)
SELECT
    w.id AS wallet_id,
    u.email,
    w.balance,
    COALESCE(t.total, 0) AS transactions_sum
FROM wallets w
JOIN users u ON u.id = w.user_id
LEFT JOIN wallet_totals t ON t.wallet_id = w.id
WHERE w.balance <> COALESCE(t.total, 0);
