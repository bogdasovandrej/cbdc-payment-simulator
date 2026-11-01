SELECT setseed(0.42);

INSERT INTO users (email, created_at)
SELECT
    'user' || n || '@example.com',
    now() - interval '60 days' + n * interval '10 hours'
FROM generate_series(1, 50) AS n;

INSERT INTO wallets (user_id)
SELECT id FROM users;

INSERT INTO payments (user_id, amount, status, created_at, updated_at)
SELECT
    user_id,
    amount,
    CASE
        WHEN r < 0.75 THEN 'PAID'
        WHEN r < 0.95 THEN 'FAILED'
        ELSE 'PROCESSING'
    END,
    created_at,
    created_at + (1 + floor(random() * 10)) * interval '1 second'
FROM (
    SELECT
        1 + floor(random() * 50)::INT AS user_id,
        round((100 + random() * 4900)::NUMERIC, 2) AS amount,
        now() - random() * interval '30 days' AS created_at,
        random() AS r
    FROM generate_series(1, 1000)
) AS p;

INSERT INTO qr_codes (payment_id, payload, expires_at)
SELECT
    id,
    'cbdc://pay?payment_id=' || id || '&amount=' || amount || '&currency=RUB',
    created_at + interval '15 minutes'
FROM payments;

INSERT INTO transactions (wallet_id, payment_id, amount, type, created_at)
SELECT w.id, p.id, p.amount, 'DEPOSIT', p.updated_at
FROM payments p
JOIN wallets w ON w.user_id = p.user_id
WHERE p.status = 'PAID';

UPDATE wallets
SET balance = (
    SELECT COALESCE(SUM(amount), 0)
    FROM transactions
    WHERE transactions.wallet_id = wallets.id
);
