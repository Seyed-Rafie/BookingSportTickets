-- in the name of GOD


-- 1. users without buying any ticket
SELECT first_name, last_name 
FROM USERS 
WHERE user_id NOT IN (SELECT DISTINCT user_id FROM RESERVATIONS);

-- 2. users who had buyed at least one ticket
SELECT DISTINCT u.first_name, u.last_name 
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
WHERE r.status = 'paid';

-- 3. sum of spending money by a user in a month
SELECT 
    u.user_id, 
    u.first_name, 
    u.last_name,
    EXTRACT(YEAR FROM p.paid_at) AS payment_year,
    EXTRACT(MONTH FROM p.paid_at) AS payment_month,
    SUM(p.amount) AS total_amount
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
WHERE p.status = 'success' AND p.paid_at IS NOT NULL
GROUP BY u.user_id, u.first_name, u.last_name, EXTRACT(YEAR FROM p.paid_at), EXTRACT(MONTH FROM p.paid_at)
ORDER BY u.user_id, payment_year, payment_month;