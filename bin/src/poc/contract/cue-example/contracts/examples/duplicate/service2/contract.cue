package service2

import "example.corp/contract-system/schema"

// Second service with duplicate name (this will cause validation error)
DuplicateService2: schema.#Contract & {
	namespace: "corp.example"
	name:      "duplicate-service"  // Same name as service1 - DUPLICATE!
	role:      "service"
	version:   "2.0.0"

	description: "Second service with duplicate namespace/name - causes validation error"

	provides: [{
		kind:        "grpc"
		port:        9090
		protocol:    "grpc"
		scope:       "internal"
		description: "gRPC API endpoint"
	}]

	dependsOn: []

	tags: ["duplicate", "test", "validation", "error"]
}