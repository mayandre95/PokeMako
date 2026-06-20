-- Référence du schéma PokéMako
-- Géré via Alembic (api/alembic/versions/)

CREATE TABLE types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE pokemon (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    hp INTEGER, attack INTEGER, defense INTEGER,
    sp_attack INTEGER, sp_defense INTEGER, speed INTEGER,
    generation INTEGER,
    is_legendary BOOLEAN DEFAULT FALSE,
    is_mythical BOOLEAN DEFAULT FALSE,
    sprite_url VARCHAR(255),
    artwork_url VARCHAR(255)
);

-- ... (voir modèles SQLAlchemy pour le schéma complet)
