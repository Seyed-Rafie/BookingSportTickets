    role_id SMALLINT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL
);

CREATE TABLE PROVINCES (
    province_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE SPORT_TYPES (
    sport_type_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE FACILITIES (
    facility_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE REPORT_CATEGORIES (
    report_category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);


CREATE TABLE CITIES (
    city_id SERIAL PRIMARY KEY,
    province_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (province_id) REFERENCES PROVINCES(province_id) ON DELETE CASCADE
);

CREATE TABLE USERS (
    user_id BIGSERIAL PRIMARY KEY,
    role_id SMALLINT NOT NULL,
    city_id INT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    profile_image_url VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES ROLES(role_id),
    FOREIGN KEY (city_id) REFERENCES CITIES(city_id) ON DELETE SET NULL
);

CREATE TABLE ORGANIZERS (
    organizer_id BIGSERIAL PRIMARY KEY,
    city_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(15),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    FOREIGN KEY (city_id) REFERENCES CITIES(city_id) ON DELETE CASCADE
);

CREATE TABLE TEAMS (
    team_id SERIAL PRIMARY KEY,
    sport_type_id INT NOT NULL,
    city_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (sport_type_id) REFERENCES SPORT_TYPES(sport_type_id),
    FOREIGN KEY (city_id) REFERENCES CITIES(city_id) ON DELETE CASCADE
);

CREATE TABLE VENUES (
    venue_id SERIAL PRIMARY KEY,
    city_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    address TEXT,
    capacity INT CHECK (capacity > 0),
    FOREIGN KEY (city_id) REFERENCES CITIES(city_id) ON DELETE CASCADE
);

CREATE TABLE COMPETITIONS (
    competition_id SERIAL PRIMARY KEY,
    sport_type_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    season VARCHAR(50),
    FOREIGN KEY (sport_type_id) REFERENCES SPORT_TYPES(sport_type_id)
);

CREATE TABLE TICKET_CATEGORIES (
    category_id SERIAL PRIMARY KEY,
    sport_type_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (sport_type_id) REFERENCES SPORT_TYPES(sport_type_id)
);


CREATE TABLE SUPPORT_USERS (
    user_id BIGINT PRIMARY KEY,
    employee_code VARCHAR(20) UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE
);

CREATE TABLE WALLETS (
    wallet_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    balance NUMERIC(15, 2) DEFAULT 0 CHECK (balance >= 0),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE
);

CREATE TABLE MATCHES (
    match_id BIGSERIAL PRIMARY KEY,
    sport_type_id INT NOT NULL,
    competition_id INT NOT NULL,
    organizer_id BIGINT NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    venue_id INT NOT NULL,
    match_datetime TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'live', 'finished', 'cancelled')),
    FOREIGN KEY (sport_type_id) REFERENCES SPORT_TYPES(sport_type_id),
    FOREIGN KEY (competition_id) REFERENCES COMPETITIONS(competition_id),
    FOREIGN KEY (organizer_id) REFERENCES ORGANIZERS(organizer_id),
    FOREIGN KEY (venue_id) REFERENCES VENUES(venue_id),
    FOREIGN KEY (home_team_id) REFERENCES TEAMS(team_id),
    FOREIGN KEY (away_team_id) REFERENCES TEAMS(team_id),
    CHECK (home_team_id != away_team_id)
);

CREATE TABLE TICKETS (
    ticket_id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL,
    category_id INT NOT NULL,
    ticket_code VARCHAR(50) UNIQUE NOT NULL,
    total_capacity INT CHECK (total_capacity > 0),
    remaining_capacity INT CHECK (remaining_capacity >= 0),
    price NUMERIC(15, 2) CHECK (price > 0),
    status VARCHAR(20) DEFAULT 'available',
    FOREIGN KEY (match_id) REFERENCES MATCHES(match_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES TICKET_CATEGORIES(category_id),
    CHECK (remaining_capacity <= total_capacity)
);

CREATE TABLE CANCELLATION_POLICIES (
    policy_id BIGSERIAL PRIMARY KEY,
    organizer_id BIGINT NOT NULL,
    sport_type_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    FOREIGN KEY (organizer_id) REFERENCES ORGANIZERS(organizer_id),
    FOREIGN KEY (sport_type_id) REFERENCES SPORT_TYPES(sport_type_id)
);



CREATE TABLE RESERVATIONS (
    reservation_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    ticket_id BIGINT NOT NULL,
    quantity INT CHECK (quantity > 0),
    status VARCHAR(20) CHECK (status IN ('reserved', 'paid', 'cancelled', 'expired')) DEFAULT 'reserved',
    total_price NUMERIC(15, 2) CHECK (total_price >= 0),
    reserved_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reserved_until TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES TICKETS(ticket_id) ON DELETE CASCADE,
    CHECK (reserved_until >= reserved_at)
);

CREATE TABLE WALLET_TRANSACTIONS (
    transaction_id BIGSERIAL PRIMARY KEY,
    wallet_id BIGINT NOT NULL,
    amount NUMERIC(15, 2) CHECK (amount <> 0),
    type VARCHAR(20) CHECK (type IN ('deposit', 'withdrawal', 'refund')) NOT NULL,
    description VARCHAR(255),
    ref_reservation_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wallet_id) REFERENCES WALLETS(wallet_id) ON DELETE CASCADE,
    FOREIGN KEY (ref_reservation_id) REFERENCES RESERVATIONS(reservation_id) ON DELETE SET NULL -- افزودن کلید خارجی گمشده
);

CREATE TABLE SEATS (
    seat_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL,
    section VARCHAR(50),
    row VARCHAR(10),
    seat_number VARCHAR(10),
    status VARCHAR(20) CHECK (status IN ('available', 'reserved', 'sold', 'blocked')) DEFAULT 'available',
    FOREIGN KEY (ticket_id) REFERENCES TICKETS(ticket_id) ON DELETE CASCADE
);

CREATE TABLE TICKET_FACILITIES (
    ticket_id BIGINT NOT NULL,
    facility_id INT NOT NULL,
    PRIMARY KEY (ticket_id, facility_id),
    FOREIGN KEY (ticket_id) REFERENCES TICKETS(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES FACILITIES(facility_id) ON DELETE CASCADE
);

CREATE TABLE FOOTBALL_DETAILS (
    ticket_id BIGINT PRIMARY KEY,
    gate_number VARCHAR(20),
    has_parking BOOLEAN DEFAULT FALSE,
    vip_services TEXT,
    FOREIGN KEY (ticket_id) REFERENCES TICKETS(ticket_id) ON DELETE CASCADE
);

CREATE TABLE VOLLEYBALL_DETAILS (
    ticket_id BIGINT PRIMARY KEY,
    entrance_gate VARCHAR(20),
    special_services TEXT,
    FOREIGN KEY (ticket_id) REFERENCES TICKETS(ticket_id) ON DELETE CASCADE
);

CREATE TABLE BASKETBALL_DETAILS (
    ticket_id BIGINT PRIMARY KEY,
    entrance_gate VARCHAR(20),
    vip_services TEXT,
    has_food_court BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (ticket_id) REFERENCES TICKETS(ticket_id) ON DELETE CASCADE
);

CREATE TABLE REPORTS (
    report_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    ticket_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    reservation_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    report_category_id INT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by_support_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    admin_response TEXT,
    submitted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES TICKETS(ticket_id) ON DELETE SET NULL,
    FOREIGN KEY (reservation_id) REFERENCES RESERVATIONS(reservation_id) ON DELETE SET NULL,
    FOREIGN KEY (report_category_id) REFERENCES REPORT_CATEGORIES(report_category_id),
    FOREIGN KEY (reviewed_by_support_id) REFERENCES SUPPORT_USERS(user_id) ON DELETE SET NULL
);



CREATE TABLE RESERVED_SEATS (
    id BIGSERIAL PRIMARY KEY,
    reservation_id BIGINT NOT NULL,
    seat_id BIGINT NOT NULL,
    status VARCHAR(20) CHECK (status IN ('active', 'released', 'cancelled')) DEFAULT 'active',
    locked_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES RESERVATIONS(reservation_id) ON DELETE CASCADE,
    FOREIGN KEY (seat_id) REFERENCES SEATS(seat_id) ON DELETE CASCADE
);

CREATE TABLE PAYMENTS (
    payment_id BIGSERIAL PRIMARY KEY,
    reservation_id BIGINT NOT NULL,
    wallet_transaction_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    amount NUMERIC(15, 2) CHECK (amount > 0),
    method VARCHAR(20) CHECK (method IN ('bank_card', 'online', 'wallet', 'fake')) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('pending', 'success', 'failed')) DEFAULT 'pending',
    paid_at TIMESTAMPTZ,
    transaction_code VARCHAR(100) UNIQUE,
    FOREIGN KEY (reservation_id) REFERENCES RESERVATIONS(reservation_id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_transaction_id) REFERENCES WALLET_TRANSACTIONS(transaction_id) ON DELETE SET NULL
);

CREATE TABLE CANCELLATION_POLICY_RULES (
    rule_id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL,
    min_hours NUMERIC(10, 2),
    max_hours NUMERIC(10, 2),
    penalty_percent NUMERIC(5, 2) CHECK (penalty_percent >= 0 AND penalty_percent <= 100),
    FOREIGN KEY (policy_id) REFERENCES CANCELLATION_POLICIES(policy_id) ON DELETE CASCADE
);

CREATE TABLE CANCELLATION_REQUESTS (
    request_id BIGSERIAL PRIMARY KEY,
    reservation_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    request_type VARCHAR(20) CHECK (request_type IN ('cancel', 'change_seat')) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    reviewed_by_support_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    requested_new_seat_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    user_note TEXT,
    admin_note TEXT,
    requested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES RESERVATIONS(reservation_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by_support_id) REFERENCES SUPPORT_USERS(user_id) ON DELETE SET NULL,
    FOREIGN KEY (requested_new_seat_id) REFERENCES SEATS(seat_id) ON DELETE SET NULL
);

CREATE TABLE REFUNDS (
    refund_id BIGSERIAL PRIMARY KEY,
    payment_id BIGINT NOT NULL,
    cancellation_request_id BIGINT NOT NULL,
    wallet_transaction_id BIGINT NULL, -- اصلاح سینتکس NULLABLE
    amount NUMERIC(15, 2) CHECK (amount > 0),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed')),
    refunded_at TIMESTAMPTZ,
    FOREIGN KEY (payment_id) REFERENCES PAYMENTS(payment_id) ON DELETE CASCADE,
    FOREIGN KEY (cancellation_request_id) REFERENCES CANCELLATION_REQUESTS(request_id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_transaction_id) REFERENCES WALLET_TRANSACTIONS(transaction_id) ON DELETE SET NULL
);
