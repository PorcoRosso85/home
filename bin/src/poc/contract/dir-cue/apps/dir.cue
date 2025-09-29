package apps

import "example.com/contracts/governance/schema"

// Sample app directory contract
_contract: schema.#DirContract & {
	srp: "Sample application directory for testing CUE contracts"
	goals: ["Demonstrate CUE contract validation", "Provide test case for checks"]
	nonGoals: ["Production usage", "Complex business logic"]
	owner:       "test-user"
	domain_path: "apps.example/sample"
}
