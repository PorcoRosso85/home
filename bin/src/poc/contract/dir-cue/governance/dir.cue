package governance

import "example.com/contracts/governance/schema"

// Governance directory contract
_contract: schema.#DirContract & {
	srp: "CUE contract schema and validation rules governance"
	goals: [
		"Define contract schemas",
		"Provide validation checks",
		"Ensure contract compliance",
	]
	nonGoals: [
		"Business logic implementation",
		"Application-specific contracts",
	]
	owner:       "governance-team"
	domain_path: "governance.contracts/schemas"
}
