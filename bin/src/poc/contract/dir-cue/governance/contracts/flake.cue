package contracts

import "example.com/contracts/governance/schema"

// Governance flake contract
_contract: schema.#FlakeContract & {
	role:  "infra"
	owner: "governance-team"
	exports: [
		{
			kind:        "lib"
			id:          "cueContractCheck"
			description: "CUE contract validation function for consumer flakes"
			scope:       "public"
		},
		{
			kind:        "lib"
			id:          "schemas"
			description: "CUE contract schema definitions"
			scope:       "public"
		},
	]
	dependsOn: []
}
