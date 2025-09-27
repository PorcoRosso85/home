package cache

import "example.corp/contract-system/schema"

// Cache service contract - provides caching capability
CacheService: schema.#Contract & {
	namespace: "corp.example"
	name:      "redis-cache"
	role:      "infra"
	version:   "2.1.0"

	description: "Redis cache service for application performance"

	provides: [{
		kind:        "cache"
		id:          "primary-cache"
		port:        6379
		protocol:    "tcp"
		scope:       "internal"
		description: "Redis cache instance for session and data caching"
	}]

	dependsOn: []

	tags: ["cache", "redis", "performance"]
}
