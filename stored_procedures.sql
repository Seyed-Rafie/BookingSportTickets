-- in the name of GOD

--1.
CREATE OR REPLACE FUNCTION sp_get_user_purchased_tickets(p_contact VARCHAR)
RETURNS TABLE (
    ticket_code VARCHAR,
    home_team VARCHAR,
    away_team VARCHAR,
    venue_name VARCHAR,
    purchased_quantity INT,
    purchase_time TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.ticket_code, 
        th.name AS home_team, 
        ta.name AS away_team, 
        v.name AS venue_name,
        r.quantity AS purchased_quantity,
        p.paid_at AS purchase_time
    FROM USERS u
    JOIN RESERVATIONS r ON u.user_id = r.user_id
    JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
    JOIN TICKETS t ON r.ticket_id = t.ticket_id
    JOIN MATCHES m ON t.match_id = m.match_id
    JOIN TEAMS th ON m.home_team_id = th.team_id
    JOIN TEAMS ta ON m.away_team_id = ta.team_id
    JOIN VENUES v ON m.venue_id = v.venue_id
    WHERE (u.email = p_contact OR u.phone = p_contact)
      AND p.status = 'success'
    ORDER BY p.paid_at DESC;
END;
$$ LANGUAGE plpgsql;
-- example: 
-- SELECT * FROM sp_get_user_purchased_tickets('09123456789');

--2.
CREATE OR REPLACE FUNCTION sp_get_users_with_cancellations(p_support_contact VARCHAR)
RETURNS TABLE (
    user_id BIGINT,
    first_name VARCHAR,
    last_name VARCHAR,
    phone VARCHAR,
    email VARCHAR
) AS $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM USERS u 
        JOIN SUPPORT_USERS su ON u.user_id = su.user_id 
        WHERE (u.email = p_support_contact OR u.phone = p_support_contact)
    ) THEN
        RETURN QUERY
        SELECT DISTINCT 
            u2.user_id, 
            u2.first_name, 
            u2.last_name, 
            u2.phone, 
            u2.email
        FROM USERS u2
        JOIN RESERVATIONS r ON u2.user_id = r.user_id
        WHERE r.status = 'cancelled';
    ELSE
        RAISE EXCEPTION 'Access Denied: The provided contact does not belong to a support user.';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- example:
-- SELECT * FROM sp_get_users_with_cancellations('support@system.com');

-- 3.
CREATE OR REPLACE FUNCTION sp_get_purchased_tickets_by_city(p_city_name VARCHAR)
RETURNS TABLE (
    ticket_code VARCHAR,
    venue_name VARCHAR,
    home_team VARCHAR,
    away_team VARCHAR,
    buyer_first_name VARCHAR,
    buyer_last_name VARCHAR,
    total_paid NUMERIC(15, 2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.ticket_code,
        v.name AS venue_name,
        th.name AS home_team,
        ta.name AS away_team,
        u.first_name AS buyer_first_name,
        u.last_name AS buyer_last_name,
        r.total_price AS total_paid
    FROM CITIES c
    JOIN VENUES v ON c.city_id = v.city_id
    JOIN MATCHES m ON v.venue_id = m.venue_id
    JOIN TICKETS t ON m.match_id = t.match_id
    JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
    JOIN USERS u ON r.user_id = u.user_id
    WHERE c.name = p_city_name 
      AND r.status = 'paid';
END;
$$ LANGUAGE plpgsql;

-- example:
-- SELECT * FROM sp_get_purchased_tickets_by_city('تهران');

--4.
CREATE OR REPLACE FUNCTION sp_search_tickets(p_search_term VARCHAR)
RETURNS TABLE (
    ticket_code VARCHAR,
    buyer_full_name VARCHAR,
    match_teams VARCHAR,
    venue_name VARCHAR,
    ticket_category VARCHAR,
    reservation_status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.ticket_code,
        (u.first_name || ' ' || u.last_name)::VARCHAR AS buyer_full_name,
        (th.name || ' vs ' || ta.name)::VARCHAR AS match_teams,
        v.name AS venue_name,
        tc.name AS ticket_category,
        r.status AS reservation_status
    FROM TICKETS t
    JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
    JOIN USERS u ON r.user_id = u.user_id
    JOIN MATCHES m ON t.match_id = m.match_id
    JOIN TEAMS th ON m.home_team_id = th.team_id
    JOIN TEAMS ta ON m.away_team_id = ta.team_id
    JOIN VENUES v ON m.venue_id = v.venue_id
    JOIN TICKET_CATEGORIES tc ON t.category_id = tc.category_id
    WHERE 
        (u.first_name ILIKE '%' || p_search_term || '%')
        OR (u.last_name ILIKE '%' || p_search_term || '%')
        OR (th.name ILIKE '%' || p_search_term || '%')
        OR (ta.name ILIKE '%' || p_search_term || '%')
        OR (v.name ILIKE '%' || p_search_term || '%')
        OR (tc.name ILIKE '%' || p_search_term || '%');
END;
$$ LANGUAGE plpgsql;

-- example:
-- SELECT * FROM sp_search_tickets('پرسپولیس');

-- SP 5: Get fellow citizens based on a user's phone number
CREATE OR REPLACE FUNCTION get_fellow_citizens(p_phone VARCHAR)
RETURNS TABLE (
    user_id BIGINT,
    first_name VARCHAR,
    last_name VARCHAR,
    phone VARCHAR,
    email VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.user_id, 
        u.first_name, 
        u.last_name, 
        u.phone, 
        u.email
    FROM USERS u
    WHERE u.city_id = (SELECT city_id FROM USERS WHERE USERS.phone = p_phone LIMIT 1)
      AND u.phone != p_phone;
END;
$$ LANGUAGE plpgsql;

-- نحوه فراخوانی (تست):
-- SELECT * FROM get_fellow_citizens('09123456789');

-- SP 6: Get top N purchased tickets by title/keyword ordered by closest match date
CREATE OR REPLACE FUNCTION get_n_nearest_tickets(p_title VARCHAR, p_n INT)
RETURNS TABLE (
    ticket_code VARCHAR,
    match_datetime TIMESTAMPTZ,
    home_team VARCHAR,
    away_team VARCHAR,
    competition_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.ticket_code,
        m.match_datetime,
        ht.name AS home_team,
        at.name AS away_team,
        c.name AS competition_name
    FROM TICKETS t
    JOIN MATCHES m ON t.match_id = m.match_id
    JOIN TEAMS ht ON m.home_team_id = ht.team_id
    JOIN TEAMS at ON m.away_team_id = at.team_id
    JOIN COMPETITIONS c ON m.competition_id = c.competition_id
    JOIN RESERVATIONS r ON t.ticket_id = r.ticket_id
    JOIN PAYMENTS p ON r.reservation_id = p.reservation_id
    WHERE p.status = 'success'
      AND (c.name ILIKE '%' || p_title || '%' 
           OR ht.name ILIKE '%' || p_title || '%' 
           OR at.name ILIKE '%' || p_title || '%')
      AND m.match_datetime >= CURRENT_DATE
    ORDER BY m.match_datetime ASC
    LIMIT p_n;
END;
$$ LANGUAGE plpgsql;

-- نحوه فراخوانی (تست):
-- SELECT * FROM get_n_nearest_tickets('پرسپولیس', 5);

-- SP 7: Get cancelled tickets by sport type ordered by match date
CREATE OR REPLACE FUNCTION get_cancelled_tickets_by_sport(p_sport_type VARCHAR)
RETURNS TABLE (
    ticket_code VARCHAR,
    match_datetime TIMESTAMPTZ,
    home_team VARCHAR,
    away_team VARCHAR,
    venue_name VARCHAR,
    reservation_status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.ticket_code,
        m.match_datetime,
        ht.name AS home_team,
        at.name AS away_team,
        v.name AS venue_name,
        r.status AS reservation_status
    FROM RESERVATIONS r
    JOIN TICKETS t ON r.ticket_id = t.ticket_id
    JOIN MATCHES m ON t.match_id = m.match_id
    JOIN TEAMS ht ON m.home_team_id = ht.team_id
    JOIN TEAMS at ON m.away_team_id = at.team_id
    JOIN VENUES v ON m.venue_id = v.venue_id
    JOIN SPORT_TYPES st ON m.sport_type_id = st.sport_type_id
    WHERE r.status = 'cancelled'
      AND st.name = p_sport_type
    ORDER BY m.match_datetime DESC;
END;
$$ LANGUAGE plpgsql;

-- نحوه فراخوانی (تست):
-- SELECT * FROM get_cancelled_tickets_by_sport('فوتبال');

-- SP 8: Get users who submitted a report under a specific category/subject
CREATE OR REPLACE FUNCTION get_users_by_report_category(p_report_category VARCHAR)
RETURNS TABLE (
    user_id BIGINT,
    first_name VARCHAR,
    last_name VARCHAR,
    phone VARCHAR,
    report_description TEXT,
    submitted_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.user_id,
        u.first_name,
        u.last_name,
        u.phone,
        rep.description AS report_description,
        rep.submitted_at
    FROM USERS u
    JOIN REPORTS rep ON u.user_id = rep.user_id
    JOIN REPORT_CATEGORIES rc ON rep.report_category_id = rc.report_category_id
    WHERE rc.name = p_report_category
    ORDER BY rep.submitted_at DESC;
END;
$$ LANGUAGE plpgsql;

-- نحوه فراخوانی (تست):
-- SELECT * FROM get_users_by_report_category('مشکل در پرداخت');