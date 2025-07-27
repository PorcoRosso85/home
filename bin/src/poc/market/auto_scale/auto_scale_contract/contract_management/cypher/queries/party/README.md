# Party Queries

This directory contains Cypher queries for managing parties (companies and individuals) in the contract management system.

## Overview

Parties are fundamental entities in the contract system that can enter into contracts as either buyers or sellers. Each party has a unique identifier and can be associated with multiple contracts through the `ContractParty` relationship.

## Query Files

### Core Party Operations

- **`create_party.cypher`** - Creates a new party node
- **`update_party.cypher`** - Updates an existing party's information
- **`find_party_by_id.cypher`** - Retrieves a party by its unique identifier
- **`ensure_party_exists.cypher`** - Upsert operation that creates or updates a party

### Contract-Party Relationships

- **`create_contract_party_relationship.cypher`** - Links a party to a contract with a specific role
- **`check_contract_party_exists.cypher`** - Verifies if a party is already linked to a contract
- **`find_parties_by_contract.cypher`** - Retrieves all parties involved in a specific contract
- **`find_contracts_by_party.cypher`** - Retrieves all contracts for a specific party

### Referral Management

- **`create_referral_chain.cypher`** - Creates a referral relationship between parties
- **`find_referral_chains.cypher`** - Queries referral relationships for commission tracking

## Usage Examples

### Creating a New Party
```cypher
:param id => 'PARTY001'
:param name => 'Acme Corporation'
:param type => 'company'
:param created_at => '2024-01-15T10:00:00Z'

CALL {
  id: $id,
  name: $name,
  type: $type,
  created_at: $created_at
}
```

### Linking a Party to a Contract
```cypher
:param contract_id => 'CONTRACT001'
:param party_id => 'PARTY001'
:param role => 'buyer'
:param joined_at => '2024-01-15T10:00:00Z'

CALL {
  contract_id: $contract_id,
  party_id: $party_id,
  role: $role,
  joined_at: $joined_at
}
```

## Data Model

### Party Node Properties
- `id` (STRING, PRIMARY KEY) - Unique identifier
- `name` (STRING) - Legal name of the party
- `type` (STRING) - Type of party (e.g., 'company', 'individual')
- `created_at` (STRING) - ISO format creation timestamp
- `tax_id` (STRING, optional) - Tax identification number

### ContractParty Relationship Properties
- `role` (STRING) - Role in the contract ('buyer' or 'seller')
- `joined_at` (STRING) - When the party joined the contract
- `commission_rate` (DOUBLE, optional) - Commission rate if applicable
- `special_terms` (STRING, optional) - Special terms for this party

### ReferralChain Relationship Properties
- `contract_id` (STRING) - Associated contract
- `referral_date` (STRING) - When the referral was made
- `commission_rate` (DOUBLE) - Commission rate for the referral

## Integration with Infrastructure Layer

These queries are used by the `KuzuGraphRepository` class in the infrastructure layer. The repository handles:
- Parameter binding
- Transaction management
- Result mapping to domain objects
- Error handling

## Best Practices

1. Always check if a party exists before creating contracts
2. Use the `ensure_party_exists.cypher` for idempotent party creation
3. Maintain referential integrity by creating parties before relationships
4. Use appropriate roles ('buyer' or 'seller') consistently
5. Include timestamps for audit trail purposes