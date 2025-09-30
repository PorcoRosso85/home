package portconflict2

import "example.corp/contract-system/schema"

// Test service that also conflicts with database port
ConflictingService2: schema.#Contract & {
	namespace: "test.example"
	name:      "conflict-service-2"
	role:      "service"
	version:   "1.0.0"

	description: "Another test service that conflicts with database port"

	provides: [{
		kind:        "worker"
		id:          "conflict-worker-2"
		port:        5432  // Same port as database
		protocol:    "tcp" // Same protocol as database
		scope:       "internal" // Same scope as database
		description: "Worker that conflicts with database port"
	}]

	dependsOn: []

	tags: ["test", "conflict"]
}