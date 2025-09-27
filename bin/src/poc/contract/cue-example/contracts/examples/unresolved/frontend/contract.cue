package frontend

import "example.corp/contract-system/schema"

// Frontend service with unresolved dependency
FrontendService: schema.#Contract & {
	namespace: "corp.example"
	name:      "web-frontend"
	role:      "app"
	version:   "1.0.0"

	description: "Web frontend application with unresolved dependencies"

	provides: [{
		kind:        "http"
		port:        3000
		protocol:    "https"
		scope:       "public"
		description: "Web application frontend"
	}]

	dependsOn: [{
		kind:         "http"
		target:       "corp.example/nonexistent-api" // This service doesn't exist!
		description:  "Backend API that doesn't exist"
		versionRange: "^1.0.0"
	}, {
		kind:         "auth"
		target:       "corp.example/missing-auth-service" // This also doesn't exist!
		description:  "Authentication service that's missing"
		versionRange: "^2.0.0"
	}]

	tags: ["frontend", "web", "unresolved", "validation-error"]
}
