package unresolved

import "example.corp/contract-system/schema"

TestContract3: schema.#Contract & {
	namespace: "corp.example"
	name:      "dependent-service"
	role:      "service"
	provides: []
	dependsOn: [{
		kind:   "db"
		target: "corp.example/nonexistent-db" // Does not exist
	}]
}
