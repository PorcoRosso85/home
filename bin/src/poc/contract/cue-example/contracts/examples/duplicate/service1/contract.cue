package service1

import "example.corp/contract-system/schema"

// First service with duplicate name (this will cause validation error)
DuplicateService1: schema.#Contract & {
	namespace: "corp.example"
	name:      "duplicate-service"  // Same name as service2
	role:      "service"
	version:   "1.0.0"

	description: "First service with duplicate namespace/name"

	provides: [{
		kind:        "http"
		port:        8081
		protocol:    "http"
		scope:       "internal"
		description: "HTTP API endpoint"
	}]

	dependsOn: []

	tags: ["duplicate", "test", "validation"]
}