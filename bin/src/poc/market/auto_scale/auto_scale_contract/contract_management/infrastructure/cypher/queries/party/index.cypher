/*
 * Party Query Index
 * 
 * This file provides an overview of all party-related queries
 * available in this directory. Each query is designed for a
 * specific operation in the contract management system.
 *
 * Query Categories:
 * 
 * 1. Core Party Operations:
 *    - create_party.cypher: Create a new party
 *    - update_party.cypher: Update existing party information
 *    - find_party_by_id.cypher: Retrieve party by ID
 *    - ensure_party_exists.cypher: Create or update party (upsert)
 *
 * 2. Contract-Party Relationships:
 *    - create_contract_party_relationship.cypher: Link party to contract
 *    - check_contract_party_exists.cypher: Check if relationship exists
 *    - find_parties_by_contract.cypher: Get all parties for a contract
 *    - find_contracts_by_party.cypher: Get all contracts for a party
 *
 * 3. Referral Management:
 *    - create_referral_chain.cypher: Create referral relationship
 *    - find_referral_chains.cypher: Query referral relationships
 *
 * Usage:
 * These queries should be executed through the KuzuGraphRepository
 * or similar data access layer that handles parameter binding and
 * transaction management.
 */

// Example: Load and execute a query
// 1. Read the query file
// 2. Bind parameters
// 3. Execute within a transaction
// 4. Map results to domain objects