INSERT INTO ROLES (role_id, role_name) VALUES 
(1, 'Admin'), 
(2, 'Customer'), 
(3, 'Support');

INSERT INTO PROVINCES (province_id, name) VALUES 
(1, 'Tehran'), 
(2, 'Esfahan');

INSERT INTO SPORT_TYPES (sport_type_id, name) VALUES 
(1, 'Football'), 
(2, 'Volleyball'), 
(3, 'Basketball');

INSERT INTO FACILITIES (facility_id, name) VALUES 
(1, 'VIP Parking'), 
(2, 'Food Court'), 
(3, 'Special Entrance');

INSERT INTO REPORT_CATEGORIES (report_category_id, name) VALUES 
(1, 'Payment Issue'), 
(2, 'Seat Problem'), 
(3, 'Ticket Fake/Scam');



INSERT INTO CITIES (city_id, province_id, name) VALUES 
(1, 1, 'Tehran'), 
(2, 2, 'Esfahan');

INSERT INTO USERS (user_id, role_id, city_id, first_name, last_name, phone, email, password_hash, status) VALUES 
(1, 2, 1, 'Ali', 'Rezaei', '09120000001', 'ali@example.com', 'hash_123', 'active'),
(2, 2, 1, 'Sara', 'Ahmadi', '09120000002', 'sara@example.com', 'hash_456', 'active'),
(3, 3, 1, 'Mohammad', 'Support', '09120000003', 'support@example.com', 'hash_789', 'active');

INSERT INTO ORGANIZERS (organizer_id, city_id, name, phone, status) VALUES 
(1, 1, 'Tehran Sports Org', '02112345678', 'active');

INSERT INTO TEAMS (team_id, sport_type_id, city_id, name) VALUES 
(1, 1, 1, 'Persepolis'),
(2, 1, 1, 'Esteghlal'),
(3, 2, 2, 'Shahrdari Vc'),
(4, 2, 2, 'Kalleh Vc');

INSERT INTO VENUES (venue_id, city_id, name, address, capacity) VALUES 
(1, 1, 'Azadi Stadium', 'West Tehran', 78000),
(2, 2, 'Felezzi Arena', 'Esfahan', 3000);

INSERT INTO COMPETITIONS (competition_id, sport_type_id, name, season) VALUES 
(1, 1, 'Persian Gulf Pro League', '2023-2024'),
(2, 2, 'Iran Volleyball Super League', '2023-2024');

INSERT INTO TICKET_CATEGORIES (category_id, sport_type_id, name) VALUES 
(1, 1, 'VIP'),
(2, 1, 'Normal'),
(3, 2, 'VIP');



INSERT INTO SUPPORT_USERS (user_id, employee_code) VALUES 
(3, 'EMP-001');

INSERT INTO WALLETS (wallet_id, user_id, balance) VALUES 
(1, 1, 1000000.00),
(2, 2, 500000.00);

INSERT INTO MATCHES (match_id, sport_type_id, competition_id, organizer_id, home_team_id, away_team_id, venue_id, match_datetime, status) VALUES 
(1, 1, 1, 1, 1, 2, 1, NOW() + INTERVAL '7 days', 'scheduled'),
(2, 2, 2, 1, 3, 4, 2, NOW() + INTERVAL '14 days', 'scheduled');

INSERT INTO TICKETS (ticket_id, match_id, category_id, ticket_code, total_capacity, remaining_capacity, price, status) VALUES 
(1, 1, 1, 'VIP-AZADI-001', 1000, 998, 500000.00, 'available'),
(2, 1, 2, 'NOR-AZADI-001', 10000, 10000, 100000.00, 'available'),
(3, 2, 3, 'VIP-VB-001', 500, 500, 150000.00, 'available');

INSERT INTO CANCELLATION_POLICIES (policy_id, organizer_id, sport_type_id, name) VALUES 
(1, 1, 1, 'Standard Football Cancellation');



INSERT INTO RESERVATIONS (reservation_id, user_id, ticket_id, quantity, status, total_price, reserved_at, reserved_until) VALUES 
(1, 1, 1, 2, 'paid', 1000000.00, NOW() - INTERVAL '2 days', NOW() + INTERVAL '1 day'),
(2, 2, 3, 1, 'paid', 150000.00, NOW() - INTERVAL '1 day', NOW() + INTERVAL '1 day');

INSERT INTO WALLET_TRANSACTIONS (transaction_id, wallet_id, amount, type, description, ref_reservation_id, created_at) VALUES 
(1, 1, -1000000.00, 'withdrawal', 'Payment for Reservation 1', 1, NOW() - INTERVAL '2 days'),
(2, 2, -150000.00, 'withdrawal', 'Payment for Reservation 2', 2, NOW() - INTERVAL '1 day');

INSERT INTO SEATS (seat_id, ticket_id, section, row_number, seat_number, status) VALUES 
(1, 1, 'A', '1', '10', 'sold'),
(2, 1, 'A', '1', '11', 'sold'),
(3, 1, 'A', '1', '12', 'available'),
(4, 2, 'B', '2', '1', 'available'),
(5, 3, 'VIP', '1', '1', 'sold');

INSERT INTO TICKET_FACILITIES (ticket_id, facility_id) VALUES 
(1, 1), (1, 3),
(3, 3);

INSERT INTO FOOTBALL_DETAILS (ticket_id, gate_number, has_parking, vip_services) VALUES 
(1, 'Gate 12', TRUE, 'Access to VIP Lounge & Catering');

INSERT INTO VOLLEYBALL_DETAILS (ticket_id, entrance_gate, special_services) VALUES 
(3, 'Gate A', 'Meet & Greet with Players');

INSERT INTO REPORTS (report_id, user_id, ticket_id, reservation_id, report_category_id, description, status, reviewed_by_support_id, admin_response, submitted_at) VALUES 
(1, 1, 1, 1, 2, 'The seat was broken.', 'pending', NULL, NULL, NOW() - INTERVAL '1 day');



INSERT INTO RESERVED_SEATS (id, reservation_id, seat_id, status, locked_at) VALUES 
(1, 1, 1, 'active', NOW() - INTERVAL '2 days'),
(2, 1, 2, 'active', NOW() - INTERVAL '2 days'),
(3, 2, 5, 'active', NOW() - INTERVAL '1 day');

INSERT INTO PAYMENTS (payment_id, reservation_id, wallet_transaction_id, amount, method, status, paid_at, transaction_code) VALUES 
(1, 1, 1, 1000000.00, 'wallet', 'success', NOW() - INTERVAL '2 days', 'TRX-WALLET-001'),
(2, 2, 2, 150000.00, 'wallet', 'success', NOW() - INTERVAL '1 day', 'TRX-WALLET-002');

INSERT INTO CANCELLATION_POLICY_RULES (rule_id, policy_id, min_hours, max_hours, penalty_percent) VALUES 
(1, 1, 48, NULL, 10.00),
(2, 1, 24, 48, 50.00),
(3, 1, 0, 24, 100.00);

INSERT INTO CANCELLATION_REQUESTS (request_id, reservation_id, user_id, request_type, status, reviewed_by_support_id, requested_new_seat_id, user_note, admin_note, requested_at) VALUES 
(1, 1, 1, 'cancel', 'approved', 3, NULL, 'I cannot attend the match due to personal reasons.', 'Approved. 10% penalty applied.', NOW() - INTERVAL '1 day');



INSERT INTO WALLET_TRANSACTIONS (transaction_id, wallet_id, amount, type, description, ref_reservation_id, created_at) VALUES 
(3, 1, 900000.00, 'refund', 'Refund for Reservation 1', 1, NOW() - INTERVAL '12 hours');

INSERT INTO REFUNDS (refund_id, payment_id, cancellation_request_id, wallet_transaction_id, amount, status, refunded_at) VALUES 
(1, 1, 1, 3, 900000.00, 'success', NOW() - INTERVAL '12 hours');

UPDATE WALLETS SET balance = balance + 900000.00 WHERE user_id = 1;

----
UPDATE RESERVATIONS SET status = 'cancelled' WHERE reservation_id = 1;

UPDATE REPORTS SET reviewed_by_support_id = 3 WHERE report_id = 1;

UPDATE PAYMENTS SET paid_at = CURRENT_TIMESTAMP WHERE payment_id = 2;