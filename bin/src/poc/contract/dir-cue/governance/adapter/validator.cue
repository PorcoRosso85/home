package adapter

import (
	"time"
	"encoding/json"
)

// ValidationEngine orchestrates dual validation of old and new contracts
#ValidationEngine: {
	// Configuration
	config: {
		strictMode: bool | *false           // Fail on warnings in strict mode
		allowlistPath: string | *"allowlist.json"
		currentDate: string                 // ISO 8601 format for expiry checking
	}

	// Input: legacy contract to validate and migrate
	input: {
		legacyContract: {...}  // Old contract structure
		targetSpecs?: {        // Optional new contract overrides
			dirContract?: {...}
			flakeContract?: {...}
		}
	}

	// Processing pipeline
	_adapter: #LegacyToNew & {
		input: input.legacyContract
	}

	_allowlist: #MigrationAllowlist & {
		// Load from external source in real implementation
	}

	// Validation results
	output: {
		// Migration result
		migration: _adapter.output

		// Dual validation status
		validation: {
			legacy: {
				valid: _validateLegacy
				errors: _legacyErrors
				warnings: _legacyWarnings
			}

			governance: {
				valid: _validateGovernance
				errors: _govErrors
				warnings: _govWarnings
			}

			compatibility: {
				compatible: _checkCompatibility
				issues: _compatibilityIssues
			}
		}

		// Overall result
		overallStatus: {
			canMigrate: _canMigrate
			requiresAllowlist: _requiresAllowlist
			recommendedAction: _recommendedAction
		}

		// Actionable guidance
		guidance: {
			immediateActions: _immediateActions
			migrationPath: _migrationPath
			riskAssessment: _riskAssessment
		}
	}

	// Internal validation logic
	_validateLegacy: (
		input.legacyContract.namespace != _|_ &&
		input.legacyContract.name != _|_ &&
		input.legacyContract.role != _|_ &&
		len(_legacyErrors) == 0
	)

	_validateGovernance: (
		_adapter.output.dirContract != _|_ &&
		_adapter.output.flakeContract != _|_ &&
		len(_govErrors) == 0
	)

	_checkCompatibility: (
		_validateLegacy && _validateGovernance &&
		len(_compatibilityIssues) == 0
	)

	_legacyErrors: [
		if input.legacyContract.namespace == _|_ { "Missing namespace in legacy contract" },
		if input.legacyContract.name == _|_ { "Missing name in legacy contract" },
		if input.legacyContract.role == _|_ { "Missing role in legacy contract" },
	]

	_legacyWarnings: [
		if input.legacyContract.description == _|_ { "Missing description - impacts SRP generation" },
		if len(input.legacyContract.provides) == 0 { "No provided capabilities" },
		if len(input.legacyContract.dependsOn) == 0 { "No dependencies declared" },
	]

	_govErrors: _adapter.output.errors

	_govWarnings: _adapter.output.warnings

	_compatibilityIssues: [
		if !_adapter.output.success { "Adapter conversion failed" },
		for warning in _adapter.output.warnings if config.strictMode {
			"Strict mode violation: " + warning
		},
	]

	_canMigrate: (
		_validateLegacy &&
		_validateGovernance &&
		(_checkCompatibility || _isAllowlisted)
	)

	_requiresAllowlist: !_checkCompatibility && _isAllowlisted

	_isAllowlisted: _allowlist.isAllowed & {
		namespace: input.legacyContract.namespace
		name: input.legacyContract.name
	}.result

	_recommendedAction:
		if _canMigrate && _checkCompatibility { "Proceed with migration" }
		else if _canMigrate && _requiresAllowlist { "Migrate with allowlist approval" }
		else if _validateLegacy && !_validateGovernance { "Fix governance schema issues" }
		else if !_validateLegacy { "Fix legacy contract issues first" }
		else { "Migration blocked - manual intervention required" }

	_immediateActions: [
		if !_validateLegacy { "Validate and fix legacy contract structure" },
		if !_validateGovernance { "Address governance schema conversion errors" },
		if len(_legacyWarnings) > 0 { "Review and address legacy contract warnings" },
		if len(_govWarnings) > 0 { "Review and address governance schema warnings" },
		if _requiresAllowlist { "Ensure allowlist approval before migration" },
	]

	_migrationPath: _adapter.output.migrationSteps

	_riskAssessment: {
		risk_level:
			if len(_legacyErrors) > 0 || len(_govErrors) > 0 { "HIGH" }
			else if len(_legacyWarnings) > 2 || len(_govWarnings) > 2 { "MEDIUM" }
			else if _requiresAllowlist { "MEDIUM" }
			else { "LOW" }

		risk_factors: [
			if len(_legacyErrors) > 0 { "Legacy contract validation errors" },
			if len(_govErrors) > 0 { "Governance schema validation errors" },
			if len(_legacyWarnings) > 2 { "Multiple legacy contract warnings" },
			if len(_govWarnings) > 2 { "Multiple governance schema warnings" },
			if _requiresAllowlist { "Requires allowlist exception" },
		]

		mitigation_steps: [
			if len(_legacyErrors) > 0 { "Fix all legacy contract errors before proceeding" },
			if len(_govErrors) > 0 { "Resolve governance schema issues" },
			if len(_legacyWarnings) > 2 { "Address legacy warnings to improve migration quality" },
			if _requiresAllowlist { "Document reason for allowlist usage and set expiry date" },
		]
	}
}

// CLI-friendly validation runner
#ValidateContract: {
	// Input contract file path or content
	contractPath: string | *""
	contractContent: {...} | *{}

	// Validation configuration
	strictMode: bool | *false
	allowlistPath: string | *"governance/adapter/allowlist.json"

	// Processing
	_engine: #ValidationEngine & {
		config: {
			strictMode: strictMode
			allowlistPath: allowlistPath
			currentDate: time.Now() // In real implementation, would use actual date
		}
		input: {
			legacyContract: contractContent
		}
	}

	// Simplified output for CLI
	result: {
		status: _engine.output.overallStatus.canMigrate
		action: _engine.output.overallStatus.recommendedAction
		risks: _engine.output.guidance.riskAssessment.risk_level
		errors: _engine.output.validation.legacy.errors + _engine.output.validation.governance.errors
		warnings: _engine.output.validation.legacy.warnings + _engine.output.validation.governance.warnings
		migration_steps: _engine.output.guidance.migrationPath
	}

	// Human-readable summary
	summary: {
		title: "Contract Migration Validation Report"
		contract_id: contractContent.namespace + "/" + contractContent.name
		timestamp: time.Now()
		overall_status:
			if _engine.output.overallStatus.canMigrate { "✅ READY FOR MIGRATION" }
			else { "❌ MIGRATION BLOCKED" }

		next_steps: _engine.output.guidance.immediateActions
	}
}