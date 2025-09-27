package api

import "example.corp/contract-system/schema"

// API service contract - depends on database and cache
ApiService: schema.#Contract & {
	namespace: "corp.example"
	name:      "user-api"
	role:      "service"
	version:   "3.4.1"

	description: "REST API service for user management"

	provides: [{
		kind:        "http"
		id:          "user-api"
		port:        8080
		protocol:    "https"
		scope:       "public"
		description: "User management REST API"
	}]

	dependsOn: [{
		kind:           "db"
		target:         "corp.example/postgres-db"
		id:             "primary-db"
		description:    "User data storage"
		versionRange:   "^1.0.0"
	}, {
		kind:           "cache"
		target:         "corp.example/redis-cache"
		id:             "primary-cache"
		description:    "Session and data caching"
		versionRange:   "^2.0.0"
		optional:       true
	}]

	tags: ["api", "users", "http", "rest"]
}