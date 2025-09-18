-- Initial migration template
-- This file establishes the starting point for your database schema
-- 
-- Naming convention: NNN_description.cypher
--   - NNN: 3-digit sequence number (000-999)
--   - description: snake_case description of the migration
--
-- Example migrations:
--   001_create_user_nodes.cypher
--   002_add_friend_relationships.cypher
--   003_create_post_nodes.cypher

-- Create initial schema
CREATE NODE TABLE User (
    id STRING PRIMARY KEY,
    name STRING NOT NULL,
    email STRING UNIQUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE NODE TABLE Post (
    id STRING PRIMARY KEY,
    title STRING NOT NULL,
    content STRING,
    created_at TIMESTAMP DEFAULT now()
);

CREATE REL TABLE Follows (
    FROM User TO User,
    followed_at TIMESTAMP DEFAULT now()
);

CREATE REL TABLE Author (
    FROM Post TO User,
    published_at TIMESTAMP DEFAULT now()
);
