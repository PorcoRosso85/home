# Kuzu Database Initialization Script
# Initialize Kuzu database with CSV data

set -e  # Exit on error

# Configuration
DB_PATH="/home/nixos/bin/src/kuzu/kuzu_db"
DATA_DIR="/home/nixos/bin/src/kuzu/data"
KUZU_CLI="kuzu"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Kuzu Database Initialization Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if kuzu CLI is installed
if ! command -v $KUZU_CLI &> /dev/null; then
    echo -e "${RED}Error: kuzu CLI not found. Please install kuzu first.${NC}"
    exit 1
fi

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}Error: Data directory $DATA_DIR not found.${NC}"
    exit 1
fi

# Clean up existing database if exists
if [ -d "$DB_PATH" ]; then
    echo -e "${YELLOW}Removing existing database at $DB_PATH...${NC}"
    rm -rf "$DB_PATH"
fi

# Create temporary Cypher script
CYPHER_SCRIPT=$(mktemp /tmp/kuzu_init.XXXXXX.cypher)

cat > "$CYPHER_SCRIPT" << 'EOF'
// ========================================
// 1. Create Schema
// ========================================
// Create VersionState node table (simplified schema)
CREATE NODE TABLE VersionState (
    version_id STRING,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    PRIMARY KEY(version_id)
);

// Create LocationURI node table (simplified schema)
CREATE NODE TABLE LocationURI (
    id STRING,
    PRIMARY KEY(id)
);

// Create CodeEntity node table
CREATE NODE TABLE CodeEntity (
    persistent_id STRING,
    name STRING,
    type STRING,
    signature STRING,
    complexity INT64,
    start_position INT64,
    end_position INT64,
    PRIMARY KEY(persistent_id)
);

// Create RequirementEntity node table
CREATE NODE TABLE RequirementEntity (
    id STRING,
    title STRING,
    description STRING,
    priority STRING,
    requirement_type STRING,
    verification_required BOOLEAN,
    PRIMARY KEY(id)
);

// Create TRACKS_STATE_OF_LOCATED_ENTITY relationship table
CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (
    FROM VersionState TO LocationURI,
    change_type STRING,
    MANY_MANY
);

// Create FOLLOWS relationship table
CREATE REL TABLE FOLLOWS (
    FROM VersionState TO VersionState,
    MANY_MANY
);

// Create CONTAINS_LOCATION relationship table
CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI,
    relation_type STRING,
    MANY_MANY
);

// Create LOCATED_WITH relationship table
CREATE REL TABLE LOCATED_WITH (
    FROM LocationURI TO CodeEntity,
    entity_type STRING,
    MANY_MANY
);

// Create IS_IMPLEMENTED_BY relationship table
CREATE REL TABLE IS_IMPLEMENTED_BY (
    FROM RequirementEntity TO CodeEntity,
    implementation_type STRING,
    MANY_MANY
);

// Create IS_VERIFIED_BY relationship table
CREATE REL TABLE IS_VERIFIED_BY (
    FROM RequirementEntity TO CodeEntity,
    test_type STRING,
    MANY_MANY
);

// Create TESTS relationship table
CREATE REL TABLE TESTS (
    FROM CodeEntity TO CodeEntity,
    test_type STRING,
    MANY_MANY
);

// ========================================
// 2. Load Data from CSV files
// ========================================
// Load VersionState nodes
COPY VersionState FROM '/home/nixos/bin/src/kuzu/data/version_states.csv' (header=true);

// Load LocationURI nodes
COPY LocationURI FROM '/home/nixos/bin/src/kuzu/data/location_uris.csv' (header=true);

// Load TRACKS_STATE_OF_LOCATED_ENTITY relationships
COPY TRACKS_STATE_OF_LOCATED_ENTITY FROM '/home/nixos/bin/src/kuzu/data/version_location_changes.csv' (header=true, FROM='version_id', TO='id');

// Load FOLLOWS relationships
COPY FOLLOWS FROM '/home/nixos/bin/src/kuzu/data/version_follows.csv' (header=true, FROM='from_version_id', TO='to_version_id');

// Load CONTAINS_LOCATION relationships
COPY CONTAINS_LOCATION FROM '/home/nixos/bin/src/kuzu/data/location_hierarchy.csv' (header=true, FROM='parent_id', TO='child_id');

// Load CodeEntity nodes
COPY CodeEntity FROM '/home/nixos/bin/src/kuzu/data/code_entities.csv' (header=true);

// Load RequirementEntity nodes
COPY RequirementEntity FROM '/home/nixos/bin/src/kuzu/data/requirement_entities.csv' (header=true);

// Load LOCATED_WITH relationships
COPY LOCATED_WITH FROM '/home/nixos/bin/src/kuzu/data/located_with.csv' (header=true, FROM='from_id', TO='to_id');

// Load IS_IMPLEMENTED_BY relationships
COPY IS_IMPLEMENTED_BY FROM '/home/nixos/bin/src/kuzu/data/is_implemented_by.csv' (header=true, FROM='from_id', TO='to_id');

// Load IS_VERIFIED_BY relationships
COPY IS_VERIFIED_BY FROM '/home/nixos/bin/src/kuzu/data/is_verified_by.csv' (header=true, FROM='from_id', TO='to_id');

// Load TESTS relationships
COPY TESTS FROM '/home/nixos/bin/src/kuzu/data/tests.csv' (header=true, FROM='from_id', TO='to_id');

// ========================================
// 3. Verification Queries
// ========================================
// Check VersionState count
MATCH (v:VersionState) RETURN count(v) as version_count;

// Check LocationURI count
MATCH (l:LocationURI) RETURN count(l) as location_count;

// Check TRACKS_STATE_OF_LOCATED_ENTITY relationships
MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI) 
RETURN count(r) as tracks_count;

// Check FOLLOWS relationships
MATCH (v1:VersionState)-[r:FOLLOWS]->(v2:VersionState) 
RETURN count(r) as follows_count;

// Check CONTAINS_LOCATION relationships
MATCH (l1:LocationURI)-[r:CONTAINS_LOCATION]->(l2:LocationURI) 
RETURN count(r) as contains_count;

// Display version lineage
MATCH (v1:VersionState)-[:FOLLOWS]->(v2:VersionState)
RETURN v1.version_id as from_version, v2.version_id as to_version
ORDER BY v1.version_id;

// Display sample data
MATCH (v:VersionState)
RETURN v.version_id, v.timestamp, v.description
ORDER BY v.timestamp
LIMIT 5;

// Check locations per version
MATCH (v:VersionState)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
WITH v.version_id as version, count(l) as location_count
RETURN version, location_count
ORDER BY version;

EOF

# Execute the script
echo -e "${YELLOW}Creating database and loading data...${NC}"
$KUZU_CLI "$DB_PATH" < "$CYPHER_SCRIPT"

# Clean up temporary file
rm -f "$CYPHER_SCRIPT"

# Execute post-processing to fix orphan LocationURIs
echo -e "${YELLOW}Running post-processing to ensure data consistency...${NC}"
$KUZU_CLI "$DB_PATH" < "/home/nixos/bin/src/kuzu/query/dml/fix_orphan_locationuris.cypher"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database initialization completed!${NC}"
echo -e "${GREEN}Database location: $DB_PATH${NC}"
echo -e "${GREEN}========================================${NC}"

# Optional: Launch interactive Kuzu CLI
echo -e "${YELLOW}To interact with the database, run:${NC}"
echo -e "  ${GREEN}kuzu $DB_PATH${NC}"
