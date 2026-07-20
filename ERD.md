erDiagram

%%====================================================
%% Relationships
%%====================================================

CITY ||--o{ USER : lives_in
CITY ||--o{ VENUE : contains
CITY ||--o{ TEAM : belongs_to

SPORTTYPE ||--o{ MATCH : has

TEAM ||--o{ MATCH : home_team
TEAM ||--o{ MATCH : away_team

VENUE ||--o{ MATCH : hosts

MATCH ||--o{ TICKET : includes

TICKETCATEGORY ||--o{ TICKET : classifies

USER ||--o{ RESERVATION : makes

TICKET ||--o{ RESERVATION : reserved

RESERVATION ||--o{ PAYMENT : payments

USER ||--o{ REPORT : creates

RESERVATION ||--o{ REPORT : related_to

%% Changed to One-to-Zero-or-One (Optional) to reflect real-world logic
MATCH ||--o| FOOTBALLDETAILS : football
MATCH ||--o| VOLLEYBALLDETAILS : volleyball
MATCH ||--o| BASKETBALLDETAILS : basketball


%%====================================================
%% Tables
%%====================================================

CITY {
    int city_id PK
    string province
    string city_name
}

TEAM {
    int team_id PK
    int city_id FK
    string team_name
}

VENUE {
    int venue_id PK
    int city_id FK
    string venue_name
    string address
    int capacity "CHECK > 0"
}

SPORTTYPE {
    int sport_type_id PK
    string sport_name
}

MATCH {
    int match_id PK
    int sport_type_id FK
    int venue_id FK
    int home_team_id FK
    int away_team_id FK
    string tournament
    datetime match_datetime
    varchar match_status
}

TICKETCATEGORY {
    int category_id PK
    string category_name
    string description
}

USER {
    int user_id PK
    int city_id FK
    string username UK
    string first_name
    string last_name
    string email UK
    string phone_number UK
    string password_hash
    varchar role "CHECK spectator/admin"
    varchar account_status
    datetime register_date
    datetime updated_at
}

TICKET {
    int ticket_id PK
    int match_id FK
    int category_id FK
    string section "Composite UK"
    int row_number "Composite UK"
    int seat_number "Composite UK"
    decimal price "CHECK >= 0"
    varchar ticket_status
    datetime created_at
}

FOOTBALLDETAILS {
    int match_id PK,FK
    string league
    string referee
    json amenities
}

VOLLEYBALLDETAILS {
    int match_id PK,FK
    string league
    string court_type
    json amenities
}

BASKETBALLDETAILS {
    int match_id PK,FK
    string league
    int quarter_duration
    json amenities
}

RESERVATION {
    int reservation_id PK
    int user_id FK
    int ticket_id FK
    varchar reservation_status
    datetime reservation_time
    datetime expiry_time "CHECK > reservation_time"
}

PAYMENT {
    int payment_id PK
    int reservation_id FK
    decimal amount
    string gateway
    string payment_method
    varchar payment_status
    string transaction_id UK
    datetime payment_time
}

REPORT {
    int report_id PK
    int user_id FK
    int reservation_id FK
    string subject
    string description
    varchar report_status
    datetime created_at
    datetime updated_at
}