-- Tabel pentru statistici de ocupabilitate items
-- Stochează date despre ocupabilitatea items pe fiecare zi din săptămână și oră

CREATE TABLE IF NOT EXISTS core_item_occupancy_stats (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL,
    weekday VARCHAR(20) NOT NULL,  -- Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    count INTEGER NOT NULL DEFAULT 0,
    max_count INTEGER NOT NULL DEFAULT 0,
    popularity INTEGER NOT NULL DEFAULT 0 CHECK (popularity >= 0 AND popularity <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key către core_item
    CONSTRAINT fk_item_occupancy_stats_item 
        FOREIGN KEY (item_id) 
        REFERENCES core_item(id) 
        ON DELETE CASCADE,
    
    -- Constraint pentru a asigura unicitatea: un item poate avea o singură înregistrare per weekday+hour
    CONSTRAINT unique_item_weekday_hour 
        UNIQUE (item_id, weekday, hour)
);

-- Index pentru performanță
CREATE INDEX IF NOT EXISTS idx_item_occupancy_stats_item_id 
    ON core_item_occupancy_stats(item_id);

CREATE INDEX IF NOT EXISTS idx_item_occupancy_stats_weekday_hour 
    ON core_item_occupancy_stats(weekday, hour);

-- Comentarii pentru claritate
COMMENT ON TABLE core_item_occupancy_stats IS 'Statistici de ocupabilitate pentru items pe fiecare zi din săptămână și oră';
COMMENT ON COLUMN core_item_occupancy_stats.item_id IS 'ID-ul item-ului (FK către core_item)';
COMMENT ON COLUMN core_item_occupancy_stats.weekday IS 'Ziua săptămânii (Monday, Tuesday, etc.)';
COMMENT ON COLUMN core_item_occupancy_stats.hour IS 'Ora (0-23)';
COMMENT ON COLUMN core_item_occupancy_stats.count IS 'Numărul de rezervări în acest slot';
COMMENT ON COLUMN core_item_occupancy_stats.max_count IS 'Numărul maxim de rezervări în acest slot';
COMMENT ON COLUMN core_item_occupancy_stats.popularity IS 'Procentul de popularitate (0-100)';

