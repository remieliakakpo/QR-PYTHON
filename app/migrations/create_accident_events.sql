-- Exécuter dans PostgreSQL Railway
-- Ouvre le terminal Railway ou psql et colle ce SQL

CREATE TABLE IF NOT EXISTS accident_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,
    qr_token        VARCHAR(255),
    latitude        FLOAT NOT NULL,
    longitude       FLOAT NOT NULL,
    zone_name       VARCHAR(500),
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    hour_of_day     INTEGER,
    day_of_week     INTEGER,
    vehicle_type    VARCHAR(50) DEFAULT 'moto',
    severity        VARCHAR(50) DEFAULT 'unknown',
    road_type       VARCHAR(100),
    weather         VARCHAR(100),
    cause_probable  VARCHAR(500),
    is_hotspot      BOOLEAN DEFAULT FALSE,
    resolved        BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ
);

-- Index pour les requêtes géographiques (très important pour les performances)
CREATE INDEX IF NOT EXISTS idx_accidents_coords 
    ON accident_events (latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_accidents_timestamp 
    ON accident_events (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_accidents_hotspot 
    ON accident_events (is_hotspot) WHERE is_hotspot = TRUE;