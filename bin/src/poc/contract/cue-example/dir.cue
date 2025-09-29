package main

import "example.com/contracts/governance/schema"

// CUE Contract Management System directory-level contract
// Follows #DirContract schema - POLICY ONLY (no implementation details)
cueExampleContract: schema.#DirContract & {
	// 単一責務原則：CUE契約システムの実用例と教育リソース提供
	srp: "Provide practical examples and educational resources for CUE contract governance"

	// プロジェクト目標（方針レベル）
	goals: [
		"Demonstrate CUE contract best practices",
		"Provide reusable contract templates",
		"Enable SSOT-based flake governance",
		"Support educational contract validation"
	]

	// 明示的な非目標（責務境界明確化）
	nonGoals: [
		"Provide production contract validation services",
		"Replace application-specific contract systems",
		"Implement runtime contract enforcement",
		"Manage external system integrations"
	]

	// プロジェクト責任者
	owner: "governance-team"

	// ドメイン階層での位置
	domain_path: "poc.contract/cue-example"
}