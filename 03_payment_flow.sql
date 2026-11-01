INSERT INTO users (email) VALUES ('test@example.com');

INSERT INTO wallets (user_id)
SELECT id FROM users WHERE email = 'test@example.com';

INSERT INTO payments (user_id, amount)
SELECT id, 1500.00 FROM users WHERE email = 'test@example.com';

INSERT INTO qr_codes (payment_id, payload, expires_at)
SELECT
    id,
    'cbdc://pay?payment_id=' || id || '&amount=' || amount || '&currency=RUB',
    now() + interval '15 minutes'
FROM payments
WHERE id = (SELECT MAX(id) FROM payments);

UPDATE payments
SET status = 'PROCESSING', updated_at = now()
WHERE id = (SELECT MAX(id) FROM payments)
  AND status = 'CREATED';

BEGIN;

UPDATE payments
SET status = 'PAID', updated_at = now()
WHERE id = (SELECT MAX(id) FROM payments)
  AND status = 'PROCESSING';

UPDATE wallets
SET balance = balance + 1500.00
WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com');

INSERT INTO transactions (wallet_id, payment_id, amount, type)
SELECT w.id, p.id, p.amount, 'DEPOSIT'
FROM payments p
JOIN wallets w ON w.user_id = p.user_id
WHERE p.id = (SELECT MAX(id) FROM payments);

COMMIT;

SELECT p.id, p.amount, p.status, q.payload, w.balance
FROM payments p
JOIN qr_codes q ON q.payment_id = p.id
JOIN wallets w ON w.user_id = p.user_id
WHERE p.id = (SELECT MAX(id) FROM payments);
