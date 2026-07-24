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

-- 4. users who had buyed a ticket only once
SELECT u.user_id, u.first_name, u.last_name
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN TICKETS t ON r.ticket_id = t.ticket_id
JOIN MATCHES m ON t.match_id = m.match_id
JOIN VENUES v ON m.venue_id = v.venue_id
WHERE r.status = 'paid'
GROUP BY u.user_id, u.first_name, u.last_name
HAVING COUNT(r.reservation_id) = COUNT(DISTINCT v.city_id);

-- 5. user who has buyed a ticker most recently
SELECT u.* FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
WHERE p.status = 'success'
ORDER BY p.paid_at DESC
LIMIT 1;

-- 6. information of users who had buyed ticket more than average
SELECT u.email, u.phone 
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
WHERE p.status = 'success'
GROUP BY u.user_id, u.email, u.phone
HAVING SUM(p.amount) > (
    SELECT AVG(user_total)
    FROM (
        SELECT SUM(p2.amount) AS user_total
        FROM PAYMENTS p2
        JOIN RESERVATIONS r2 ON p2.reservation_id = r2.reservation_id
        WHERE p2.status = 'success'
        GROUP BY r2.user_id
    ) AS subquery
);

-- 7. number of sold tickets by a type of sport
SELECT st.name AS sport_name, COALESCE(SUM(r.quantity), 0) AS tickets_sold
FROM SPORT_TYPES st
LEFT JOIN MATCHES m ON st.sport_type_id = m.sport_type_id
LEFT JOIN TICKETS t ON m.match_id = t.match_id
LEFT JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id AND r.status = 'paid'
GROUP BY st.sport_type_id, st.name;

-- 8. name of 3 users who had most buyed ticket in a week
SELECT u.first_name, u.last_name, SUM(r.quantity) AS total_tickets_bought
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
WHERE p.status = 'success' AND p.paid_at >= NOW() - INTERVAL '7 days'
GROUP BY u.user_id, u.first_name, u.last_name
ORDER BY total_tickets_bought DESC
LIMIT 3;

-- 9. numbers of sold tickets in Tehran province
SELECT c.name AS city_name, SUM(r.quantity) AS tickets_sold
FROM PROVINCES pr
JOIN CITIES c ON pr.province_id = c.province_id
JOIN VENUES v ON c.city_id = v.city_id
JOIN MATCHES m ON v.venue_id = m.venue_id
JOIN TICKETS t ON m.match_id = t.match_id
JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
WHERE pr.name = 'تهران' AND r.status = 'paid'
GROUP BY c.city_id, c.name;

-- 10. cities that oldest user had buyed ticket from that
SELECT DISTINCT c.name AS city_name
FROM CITIES c
JOIN VENUES v ON c.city_id = v.city_id
JOIN MATCHES m ON v.venue_id = m.venue_id
JOIN TICKETS t ON m.match_id = t.match_id
JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
WHERE r.status = 'paid' AND r.user_id = (
    SELECT user_id 
    FROM USERS 
    ORDER BY created_at ASC 
    LIMIT 1
);

-- 11. information of supports
SELECT DISTINCT c.name AS city_name
FROM CITIES c
JOIN VENUES v ON c.city_id = v.city_id
JOIN MATCHES m ON v.venue_id = m.venue_id
JOIN TICKETS t ON m.match_id = t.match_id
JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
WHERE r.status = 'paid' AND r.user_id = (
    SELECT user_id 
    FROM USERS 
    ORDER BY created_at ASC 
    LIMIT 1
);

-- Query 12: Users who bought at least 2 tickets
SELECT 
    u.user_id,
    u.first_name,
    u.last_name,
    SUM(r.quantity) AS total_tickets_bought
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
WHERE p.status = 'success' OR r.status = 'paid'
GROUP BY u.user_id, u.first_name, u.last_name
HAVING SUM(r.quantity) >= 2;

-- Query 13: Users who bought at most 2 tickets for a specific sport (e.g., Football)
SELECT 
    u.user_id,
    u.first_name,
    u.last_name,
    SUM(r.quantity) AS football_tickets_bought
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
JOIN TICKETS t ON r.ticket_id = t.ticket_id
JOIN MATCHES m ON t.match_id = m.match_id
JOIN SPORT_TYPES st ON m.sport_type_id = st.sport_type_id
WHERE (p.status = 'success' OR r.status = 'paid')
  AND st.name = 'Football'
GROUP BY u.user_id, u.first_name, u.last_name
HAVING SUM(r.quantity) <= 2;

-- Query 14: Users who bought tickets for ALL available sport types
SELECT 
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    u.phone
FROM USERS u
JOIN RESERVATIONS r ON u.user_id = r.user_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
JOIN TICKETS t ON r.ticket_id = t.ticket_id
JOIN MATCHES m ON t.match_id = m.match_id
JOIN SPORT_TYPES st ON m.sport_type_id = st.sport_type_id
WHERE p.status = 'success' OR r.status = 'paid'
GROUP BY u.user_id, u.first_name, u.last_name, u.email, u.phone
HAVING COUNT(DISTINCT st.sport_type_id) = (SELECT COUNT(*) FROM SPORT_TYPES);

-- Query 15: Tickets purchased today ordered by time
SELECT 
    t.ticket_code,
    r.quantity,
    p.amount AS total_paid,
    p.paid_at,
    u.first_name,
    u.last_name
FROM TICKETS t
JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
JOIN USERS u ON r.user_id = u.user_id
WHERE p.status = 'success' 
  AND p.paid_at::DATE = CURRENT_DATE
ORDER BY p.paid_at ASC;

-- Query 16: The second best-selling ticket
SELECT 
    t.ticket_id,
    t.ticket_code,
    m.match_datetime,
    SUM(r.quantity) AS total_sold
FROM TICKETS t
JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
JOIN MATCHES m ON t.match_id = m.match_id
WHERE p.status = 'success'
GROUP BY t.ticket_id, t.ticket_code, m.match_datetime
ORDER BY total_sold DESC
LIMIT 1 OFFSET 1;

-- Query 17: Support admin with the most cancellations and their percentage
WITH TotalCancellations AS (
    SELECT COUNT(*) AS total_count
    FROM CANCELLATION_REQUESTS
    WHERE request_type = 'cancel' AND status = 'approved'
),
SupportCancellations AS (
    SELECT 
        reviewed_by_support_id,
        COUNT(request_id) AS support_cancel_count
    FROM CANCELLATION_REQUESTS
    WHERE request_type = 'cancel' AND status = 'approved' AND reviewed_by_support_id IS NOT NULL
    GROUP BY reviewed_by_support_id
)
SELECT 
    u.first_name,
    u.last_name,
    su.employee_code,
    sc.support_cancel_count AS total_cancellations_handled,
    ROUND((sc.support_cancel_count * 100.0) / tc.total_count, 2) AS cancellation_percentage
FROM SupportCancellations sc
JOIN SUPPORT_USERS su ON sc.reviewed_by_support_id = su.user_id
JOIN USERS u ON su.user_id = u.user_id
CROSS JOIN TotalCancellations tc
ORDER BY sc.support_cancel_count DESC
LIMIT 1;

-- Query 18: Update the last name of the user with the most cancelled tickets to 'ردینگتون'
UPDATE USERS
SET last_name = 'ردینگتون'
WHERE user_id = (
    SELECT u.user_id
    FROM USERS u
    JOIN RESERVATIONS r ON u.user_id = r.user_id
    WHERE r.status = 'cancelled'
    GROUP BY u.user_id
    ORDER BY COUNT(r.reservation_id) DESC
    LIMIT 1
);

-- Query 19: Delete all cancelled reservations/tickets of user 'ردینگتون'
DELETE FROM RESERVATIONS
WHERE status = 'cancelled'
  AND user_id IN (
      SELECT user_id 
      FROM USERS 
      WHERE last_name = 'ردینگتون'
  );

  -- Query 20: Delete all cancelled reservations in the system
DELETE FROM RESERVATIONS
WHERE status = 'cancelled';

-- Query 21: Reduce the price of tickets sold yesterday for matches at Azadi Stadium by 10%
UPDATE TICKETS
SET price = price * 0.90
WHERE ticket_id IN (
    SELECT t.ticket_id
    FROM TICKETS t
    JOIN MATCHES m ON t.match_id = m.match_id
    JOIN VENUES v ON m.venue_id = v.venue_id
    JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
    JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
    WHERE v.name ILIKE '%Azadi%'
      AND p.paid_at::DATE = CURRENT_DATE - INTERVAL '1 day'
);

-- Query 22: Support admin name along with report subject/category and total count
SELECT 
    u.first_name AS support_first_name,
    u.last_name AS support_last_name,
    su.employee_code,
    rc.name AS report_category_name,
    COUNT(rep.report_id) AS total_reports_handled
FROM REPORTS rep
JOIN SUPPORT_USERS su ON rep.reviewed_by_support_id = su.user_id
JOIN USERS u ON su.user_id = u.user_id
JOIN REPORT_CATEGORIES rc ON rep.report_category_id = rc.report_category_id
WHERE rep.reviewed_by_support_id IS NOT NULL
GROUP BY u.first_name, u.last_name, su.employee_code, rc.name
ORDER BY total_reports_handled DESC;