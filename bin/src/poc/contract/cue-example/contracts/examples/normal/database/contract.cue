package database

import "example.corp/contract-system/schema"

// Database service contract - provides database capability
DatabaseService: schema.#Contract & {
	namespace: "corp.example"
	name:      "postgres-db"
	role:      "infra"
	version:   "1.2.0"

	description: "PostgreSQL database service for application data"

	provides: [{
		kind:        "db"
		id:          "primary-db"
		port:        5432
		protocol:    "tcp"
		scope:       "internal"
		description: "Main PostgreSQL database instance"
	}]

	dependsOn: []

	tags: ["database", "postgresql", "storage"]
}