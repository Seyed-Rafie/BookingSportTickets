CREATE INDEX idx_matches_datetime ON MATCHES(match_datetime);
CREATE INDEX idx_matches_sport_city ON MATCHES(sport_type_id, venue_id);
CREATE INDEX idx_tickets_match_id ON TICKETS(match_id);
CREATE INDEX idx_tickets_status ON TICKETS(status);
CREATE INDEX idx_reservations_user_status ON RESERVATIONS(user_id, status);
CREATE INDEX idx_users_phone ON USERS(phone);
CREATE INDEX idx_users_email ON USERS(email);
CREATE INDEX idx_seats_ticket_status ON SEATS(ticket_id, status);
CREATE INDEX idx_reports_status ON REPORTS(status);