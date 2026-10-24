CREATE TABLE IF NOT EXISTS daily_missions (
    mission_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,
    mission TEXT NOT NULL,

    PRIMARY KEY (mission_date, category)
);