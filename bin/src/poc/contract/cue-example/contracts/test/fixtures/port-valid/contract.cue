package portvalid

import "example.corp/contract-system/schema"

// Test service with unique port that should not conflict
ValidService: schema.#Contract & {
	namespace: "test.example"
	name:      "valid-service"
	role:      "service"
	version:   "1.0.0"

	description: "Test service with unique port assignment"

	provides: [{
		kind:        "api"
		id:          "valid-api"
		port:        9999  // Unique port
		protocol:    "tcp"
		scope:       "internal"
		description: "API with unique port assignment"
	}]

	dependsOn: []

	tags: ["test", "valid"]
}