erDiagram
    PROVINCES ||--o{ CITIES : "has"
    CITIES ||--o{ USERS : "locates"
    CITIES ||--o{ ORGANIZERS : "locates"
    CITIES ||--o{ VENUES : "locates"
    CITIES ||--o{ TEAMS : "locates"
    
    ROLES ||--o{ USERS : "classifies"
    USERS ||--o| SUPPORT_USERS : "is a"
    USERS ||--o| WALLETS : "owns"
    WALLETS ||--o{ WALLET_TRANSACTIONS : "logs"
    
    SPORT_TYPES ||--o{ TEAMS : "categorizes"
    SPORT_TYPES ||--o{ COMPETITIONS : "categorizes"
    SPORT_TYPES ||--o{ MATCHES : "categorizes"
    SPORT_TYPES ||--o{ CANCELLATION_POLICIES : "applies to"
    SPORT_TYPES ||--o{ TICKET_CATEGORIES : "categorizes"
    
    TEAMS ||--o{ MATCHES : "home team"
    TEAMS ||--o{ MATCHES : "away team"
    COMPETITIONS ||--o{ MATCHES : "hosts"
    ORGANIZERS ||--o{ MATCHES : "organizes"
    ORGANIZERS ||--o{ CANCELLATION_POLICIES : "creates"
    VENUES ||--o{ MATCHES : "hosts"
    
    MATCHES ||--o{ TICKETS : "offers"
    TICKET_CATEGORIES ||--o{ TICKETS : "classifies"
    FACILITIES ||--o{ TICKET_FACILITIES : "includes"
    TICKETS ||--o{ TICKET_FACILITIES : "has"
    
    TICKETS ||--o| FOOTBALL_DETAILS : "has specifics"
    TICKETS ||--o| VOLLEYBALL_DETAILS : "has specifics"
    TICKETS ||--o| BASKETBALL_DETAILS : "has specifics"
    TICKETS ||--o{ SEATS : "allocates"
    
    USERS ||--o{ RESERVATIONS : "places"
    TICKETS ||--o{ RESERVATIONS : "booked via"
    RESERVATIONS ||--o{ RESERVED_SEATS : "assigns"
    SEATS ||--o{ RESERVED_SEATS : "occupied by"
    SEATS ||--o{ CANCELLATION_REQUESTS : "requested as new"
    
    RESERVATIONS ||--o| PAYMENTS : "paid by"
    PAYMENTS ||--o{ REFUNDS : "refunded via"
    
    USERS ||--o{ CANCELLATION_REQUESTS : "submits"
    RESERVATIONS ||--o{ CANCELLATION_REQUESTS : "cancels"
    SUPPORT_USERS ||--o{ CANCELLATION_REQUESTS : "reviews"
    CANCELLATION_REQUESTS ||--o{ REFUNDS : "results in"
    
    CANCELLATION_POLICIES ||--o{ CANCELLATION_POLICY_RULES : "has rules"
    
    REPORT_CATEGORIES ||--o{ REPORTS : "classifies"
    USERS ||--o{ REPORTS : "submits"
    SUPPORT_USERS ||--o{ REPORTS : "reviews"
    TICKETS ||--o{ REPORTS : "reported about"
    RESERVATIONS ||--o{ REPORTS : "reported about"

    ROLES {
        SMALLINT role_id PK
        VARCHAR role_name
    }
    
    PROVINCES {
        SERIAL province_id PK
        VARCHAR name
    }
    
    CITIES {
        SERIAL city_id PK
        INT province_id FK
        VARCHAR name
    }
    
    USERS {
        BIGSERIAL user_id PK
        SMALLINT role_id FK
        INT city_id FK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR phone "UNIQUE"
        VARCHAR email "UNIQUE"
        VARCHAR password_hash
        VARCHAR profile_image_url
        VARCHAR status
        TIMESTAMP created_at
    }
    
    SUPPORT_USERS {
        BIGINT user_id PK, FK
        VARCHAR employee_code "UNIQUE"
    }
    
    WALLETS {
        BIGSERIAL wallet_id PK
        BIGINT user_id FK "UNIQUE"
        NUMERIC balance "CHECK >= 0"
        TIMESTAMP updated_at
    }
    
    WALLET_TRANSACTIONS {
        BIGSERIAL transaction_id PK
        BIGINT wallet_id FK
        NUMERIC amount "CHECK <> 0"
        VARCHAR type "CHECK IN (deposit, withdrawal, refund)"
        VARCHAR description
        BIGINT ref_reservation_id FK "NULLABLE"
        TIMESTAMP created_at
    }
    
    ORGANIZERS {
        BIGSERIAL organizer_id PK
        INT city_id FK
        VARCHAR name
        VARCHAR phone
        VARCHAR status
    }
    
    SPORT_TYPES {
        SERIAL sport_type_id PK
        VARCHAR name "UNIQUE"
    }
    
    TEAMS {
        SERIAL team_id PK
        INT sport_type_id FK
        INT city_id FK
        VARCHAR name
    }
    
    VENUES {
        SERIAL venue_id PK
        INT city_id FK
        VARCHAR name
        VARCHAR address
        INT capacity "CHECK > 0"
    }
    
    COMPETITIONS {
        SERIAL competition_id PK
        INT sport_type_id FK
        VARCHAR name
        VARCHAR season
    }
    
    MATCHES {
        BIGSERIAL match_id PK
        INT sport_type_id FK
        INT competition_id FK
        BIGINT organizer_id FK
        INT home_team_id FK
        INT away_team_id FK
        INT venue_id FK
        TIMESTAMP match_datetime
        VARCHAR status
    }
    
    TICKET_CATEGORIES {
        SERIAL category_id PK
        INT sport_type_id FK
        VARCHAR name
    }
    
    TICKETS {
        BIGSERIAL ticket_id PK
        BIGINT match_id FK
        INT category_id FK
        VARCHAR ticket_code "UNIQUE"
        INT total_capacity "CHECK > 0"
        INT remaining_capacity "CHECK >= 0"
        NUMERIC price "CHECK > 0"
        VARCHAR status
    }
    
    SEATS {
        BIGSERIAL seat_id PK
        BIGINT ticket_id FK
        VARCHAR section
        VARCHAR row
        VARCHAR seat_number
        VARCHAR status "CHECK IN (available, reserved, sold, blocked)"
    }
    
    FACILITIES {
        SERIAL facility_id PK
        VARCHAR name
    }
    
    TICKET_FACILITIES {
        BIGINT ticket_id PK, FK
        INT facility_id PK, FK
    }
    
    FOOTBALL_DETAILS {
        BIGINT ticket_id PK, FK
        VARCHAR gate_number
        BOOLEAN has_parking
        TEXT vip_services
    }
    
    VOLLEYBALL_DETAILS {
        BIGINT ticket_id PK, FK
        VARCHAR entrance_gate
        TEXT special_services
    }
    
    BASKETBALL_DETAILS {
        BIGINT ticket_id PK, FK
        VARCHAR entrance_gate
        TEXT vip_services
        BOOLEAN has_food_court
    }
    
    RESERVATIONS {
        BIGSERIAL reservation_id PK
        BIGINT user_id FK
        BIGINT ticket_id FK
        INT quantity "CHECK > 0"
        VARCHAR status "CHECK IN (reserved, paid, cancelled, expired)"
        NUMERIC total_price "CHECK >= 0"
        TIMESTAMP reserved_at
        TIMESTAMP reserved_until
    }
    
    RESERVED_SEATS {
        BIGSERIAL id PK
        BIGINT reservation_id FK
        BIGINT seat_id FK
        VARCHAR status "CHECK IN (active, released, cancelled)"
        TIMESTAMP locked_at
    }
    
    PAYMENTS {
        BIGSERIAL payment_id PK
        BIGINT reservation_id FK
        BIGINT wallet_transaction_id FK "NULLABLE"
        NUMERIC amount "CHECK > 0"
        VARCHAR method "CHECK IN (bank_card, online, wallet, fake)"
        VARCHAR status "CHECK IN (pending, success, failed)"
        TIMESTAMP paid_at
        VARCHAR transaction_code "UNIQUE"
    }
    
    CANCELLATION_POLICIES {
        BIGSERIAL policy_id PK
        BIGINT organizer_id FK
        INT sport_type_id FK
        VARCHAR name
    }
    
    CANCELLATION_POLICY_RULES {
        BIGSERIAL rule_id PK
        BIGINT policy_id FK
        NUMERIC min_hours
        NUMERIC max_hours
        NUMERIC penalty_percent "CHECK >= 0 AND <= 100"
    }
    
    CANCELLATION_REQUESTS {
        BIGSERIAL request_id PK
        BIGINT reservation_id FK
        BIGINT user_id FK
        VARCHAR request_type "CHECK IN (cancel, change_seat)"
        VARCHAR status "CHECK IN (pending, approved, rejected)"
        BIGINT reviewed_by_support_id FK "NULLABLE"
        BIGINT requested_new_seat_id FK "NULLABLE, for change_seat"
        TEXT user_note
        TEXT admin_note
        TIMESTAMP requested_at
    }
    
    REFUNDS {
        BIGSERIAL refund_id PK
        BIGINT payment_id FK
        BIGINT cancellation_request_id FK
        BIGINT wallet_transaction_id FK "NULLABLE"
        NUMERIC amount "CHECK > 0"
        VARCHAR status
        TIMESTAMP refunded_at
    }
    
    REPORT_CATEGORIES {
        SERIAL report_category_id PK
        VARCHAR name
    }
    
    REPORTS {
        BIGSERIAL report_id PK
        BIGINT user_id FK
        BIGINT ticket_id FK "NULLABLE"
        BIGINT reservation_id FK "NULLABLE"
        INT report_category_id FK
        TEXT description
        VARCHAR status
        BIGINT reviewed_by_support_id FK "NULLABLE"
        TEXT admin_response
        TIMESTAMP submitted_at
    }