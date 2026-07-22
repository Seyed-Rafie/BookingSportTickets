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