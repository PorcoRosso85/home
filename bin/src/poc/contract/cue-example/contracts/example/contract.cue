package example

import "example.corp/contract-system/schema"

// Example contract following the schema
ExampleContract: schema.#Contract & {
	namespace: "corp.example"
	name:      "api-service"
	role:      "service"
	version:   "1.0.0"

	provides: [{
		kind:        "http"
		id:          "public"
		port:        8080
		protocol:    "http"
		scope:       "public"
		description: "Public REST API"
	}]

	dependsOn: [{
		kind:         "db"
		target:       "corp.example/postgres"
		id:           "primary"
		versionRange: "^13.0.0"
		description:  "Primary PostgreSQL database"
	}]

	description: "Example API service for demonstration"
	tags: ["api", "service", "example"]
}
