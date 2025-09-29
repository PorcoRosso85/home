package portconflict1

import "example.corp/contract-system/schema"

// Test service that conflicts with database port
ConflictingService1: schema.#Contract & {
	namespace: "test.example"
	name:      "conflict-service-1"
	role:      "service"
	version:   "1.0.0"

	description: "Test service that conflicts with database port"

	provides: [{
		kind:        "api"
		id:          "conflict-api-1"
		port:        5432  // Same port as database
		protocol:    "tcp" // Same protocol as database
		scope:       "internal" // Same scope as database
		description: "API that conflicts with database port"
	}]

	dependsOn: []

	tags: ["test", "conflict"]
}