package tools

import (
	"strings"
	"list"
	"example.corp/contract-system/schema"
)

// Contract aggregation and validation
#AggregateValidation: {
	contracts: [...schema.#Contract]

	// Extract all namespace/name combinations for duplicate checking
	identifiers: [for c in contracts {c.namespace + "/" + c.name}]

	// Check for duplicates by comparing list length with unique set
	duplicateCheck: {
		unique: {for id in identifiers {(id): true}}
		hasDuplicates: len(identifiers) != len(unique)

		// Create error message if duplicates found
		if hasDuplicates {
			_error: "aggregate: duplicate namespace/name found"
			// Force validation failure by creating impossible constraint
			_fail: false & true
		}
	}

	// Check dependency resolution
	dependencyCheck: {
		// All available providers (namespace/name)
		providers: [for c in contracts {c.namespace + "/" + c.name}]

		// All required dependencies
		dependencies: [for c in contracts for d in c.dependsOn {d.target}]

		// Find missing providers
		missing: [for dep in dependencies if !list.Contains(providers, dep) {dep}]

		// Create error if unresolved dependencies found
		if len(missing) > 0 {
			_error: "deps: missing provider for " + strings.Join(missing, ", ")
			// Force validation failure by creating impossible constraint
			_fail: false & true
		}
	}

	// Port conflict detection
	portCheck: {
		// Extract all used ports with their owners
		portMappings: [for c in contracts for p in c.provides if p.port != _|_ {
			port:  p.port
			owner: c.namespace + "/" + c.name
		}]

		// Simple port conflict detection (can be enhanced)
		conflicts: [] // Simplified for now

		// No error for now - can be enhanced later
	}
}

// This validation instance will be populated by the Nix build process
// with actual contract data from discovered contract files
validation: #AggregateValidation
