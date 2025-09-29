package adapter

import (
	oldSchema "example.corp/contract-system/schema"
	govSchema "example.com/contracts/governance/schema"
)

// LegacyContractAdapter provides compatibility between old #Contract schema and new governance schemas
// Purpose: Enable safe migration from old provides/dependsOn structure to new exports/dependsOn structure
// Principle: Maintain backward compatibility while enforcing new governance patterns

// #AdapterResult contains the result of legacy contract adaptation
#AdapterResult: {
	// Conversion success status
	success: bool

	// Adapted contracts using new schema
	dirContract?:   govSchema.#DirContract
	flakeContract?: govSchema.#FlakeContract

	// Validation warnings and errors
	warnings: [...string]
	errors:   [...string]

	// Migration guidance
	migrationSteps: [...string]
}

// #LegacyToNew adapts old #Contract to new governance schemas
#LegacyToNew: {
	// Input: old contract structure
	input: oldSchema.#Contract

	// Output: adapted result with new schemas
	output: #AdapterResult & {
		// Map old contract to DirContract (policy layer)
		dirContract: govSchema.#DirContract & {
			// Extract SRP from description or generate default
			srp: _extractSRP

			// Default goals if not specified
			goals: *["Provide " + input.role + " functionality"] | []
			nonGoals: *["Cross-cutting concerns outside " + input.role + " boundary"] | []

			// Map ownership if available
			if input.namespace != _|_ {
				owner: input.namespace
			}

			// Generate domain path from namespace/name
			if input.namespace != _|_ && input.name != _|_ {
				domain_path: input.namespace + "/" + input.name
			}
		}

		// Map old contract to FlakeContract (technical boundary layer)
		flakeContract: govSchema.#FlakeContract & {
			// Direct role mapping
			role: _mapRole

			// Extract owner from namespace or use default
			owner: input.namespace | "migration-pending"

			// Convert provides → exports with field mapping
			exports: [ for cap in input.provides {
				govSchema.#Export & {
					// Map capability kind to export kind
					kind: _mapCapabilityKind & cap.kind

					// Preserve optional fields where compatible
					if cap.id != _|_ { id: cap.id }
					if cap.version != _|_ { version: cap.version }
					if cap.port != _|_ { port: cap.port }
					if cap.protocol != _|_ { protocol: _mapProtocol & cap.protocol }
					if cap.scope != _|_ { scope: _mapScope & cap.scope }
					if cap.description != _|_ { description: cap.description }
				}
			}]

			// Convert dependsOn with field mapping
			dependsOn: [ for dep in input.dependsOn {
				govSchema.#DepRef & {
					// Map capability kind to dep kind
					kind: _mapCapabilityKind & dep.kind

					// Use target directly
					target: dep.target

					// Preserve optional fields where compatible
					if dep.id != _|_ { id: dep.id }
					if dep.versionRange != _|_ { versionRange: dep.versionRange }
					if dep.optional != _|_ { optional: dep.optional }
					if dep.description != _|_ { description: dep.description }
				}
			}]
		}

		// Evaluate success based on completeness
		success: _evaluateSuccess

		// Generate warnings for missing/incompatible fields
		warnings: _generateWarnings

		// Generate errors for blocking issues
		errors: _generateErrors

		// Provide step-by-step migration guidance
		migrationSteps: _generateMigrationSteps
	}

	// Internal mapping helpers
	_extractSRP: input.description | "Legacy " + input.role + " contract - requires SRP definition"

	_mapRole: {
		"service": "service"
		"lib":     "lib"
		"infra":   "infra"
		"app":     "app"
		"tool":    "tool"
	}[input.role] | input.role

	_mapCapabilityKind: {
		"http":       "http"
		"grpc":       "grpc"
		"db":         "db"
		"queue":      "service"  // Map queue to service
		"cache":      "service"  // Map cache to service
		"storage":    "service"  // Map storage to service
		"auth":       "service"  // Map auth to service
		"monitoring": "service"  // Map monitoring to service
		"logging":    "service"  // Map logging to service
		"config":     "service"  // Map config to service
		"secret":     "service"  // Map secret to service
		"dns":        "service"  // Map dns to service
		"proxy":      "service"  // Map proxy to service
		"gateway":    "service"  // Map gateway to service
	}

	_mapProtocol: {
		"tcp":       "tcp"
		"udp":       "tcp"        // Map UDP to TCP as fallback
		"http":      "http"
		"https":     "https"
		"grpc":      "grpc"
		"websocket": "https"      // Map websocket to https as fallback
	}

	_mapScope: {
		"internal": "internal"
		"public":   "public"
		"private":  "internal"    // Map private to internal
	}

	_evaluateSuccess: (
		input.namespace != _|_ &&
		input.name != _|_ &&
		input.role != _|_ &&
		len(errors) == 0
	)

	_generateWarnings: [
		if input.description == _|_ { "Missing description - will use generated SRP" },
		if len(input.provides) == 0 { "No capabilities provided - exports will be empty" },
		if input.namespace == "migration-pending" { "Namespace not specified - requires manual owner assignment" },
		if len([ for cap in input.provides if _mapCapabilityKind[cap.kind] == "service" { cap }]) > 0 {
			"Some capability kinds mapped to 'service' - consider more specific categorization"
		},
	]

	_generateErrors: [
		if !(_mapRole[input.role] != _|_) { "Unsupported role: " + input.role },
		for cap in input.provides if !(_mapCapabilityKind[cap.kind] != _|_) {
			"Unsupported capability kind: " + cap.kind
		},
		for dep in input.dependsOn if !(_mapCapabilityKind[dep.kind] != _|_) {
			"Unsupported dependency kind: " + dep.kind
		},
	]

	_generateMigrationSteps: [
		"1. Review generated SRP and replace with project-specific description",
		"2. Validate exported capabilities match intended interface contract",
		"3. Confirm dependency mappings align with actual requirements",
		if input.namespace == "migration-pending" { "4. Assign proper owner identifier" },
		"5. Test new contract with 'cue vet' command",
		"6. Gradually phase out old contract usage",
	]
}

// #DualValidator provides side-by-side validation of old and new contracts
#DualValidator: {
	// Input contracts
	oldContract: oldSchema.#Contract
	newDirContract: govSchema.#DirContract
	newFlakeContract: govSchema.#FlakeContract

	// Validation results
	oldValid: bool
	newValid: bool
	compatible: bool

	// Validation reports
	oldReport: {
		errors: [...string]
		warnings: [...string]
	}

	newReport: {
		errors: [...string]
		warnings: [...string]
	}

	compatibilityReport: {
		mismatches: [...string]
		suggestions: [...string]
	}

	// Allowlist support for gradual migration
	allowlistExceptions: [...string]
	isAllowlisted: bool
}

// #MigrationAllowlist manages temporary exceptions during migration period
#MigrationAllowlist: {
	// Allowlisted contracts with expiration dates
	entries: [...{
		namespace: string
		name: string
		reason: string
		expiryDate: string  // ISO 8601 format
		contact: string     // Responsible person
	}]

	// Check if a contract is allowlisted
	isAllowed: {
		namespace: string
		name: string
		result: bool
		// Logic to check if namespace/name combo is in entries and not expired
	}
}