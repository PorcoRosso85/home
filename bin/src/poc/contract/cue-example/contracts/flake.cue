package contracts

import "example.com/contracts/governance/schema"

// CUE Example flake contract - BOUNDARY ONLY (technical interface specification)
// Follows #FlakeContract schema - no policy details (those are in dir.cue)
flakeContract: schema.#FlakeContract & {
	// Flake種別：ツール類（開発者向けユーティリティ）
	role: "tool"

	// 技術責任者
	owner: "governance-team"

	// 対外提供インターフェース（技術境界）
	exports: [
		{
			kind:        "cli"
			id:          "cue-validate"
			description: "CUE contract validation command line interface"
			scope:       "public"
		},
		{
			kind:        "lib"
			id:          "contract-templates"
			description: "Reusable CUE contract template library"
			scope:       "public"
		},
		{
			kind:        "service"
			id:          "contract-check"
			description: "Automated contract validation service for CI/CD"
			scope:       "internal"
		}
	]

	// 外部flake依存関係（inputs）
	dependsOn: [
		{
			kind:         "lib"
			target:       "github:NixOS/nixpkgs"
			id:           "nixpkgs"
			description:  "Standard Nix package collection"
			versionRange: "nixos-unstable"
		},
		{
			kind:         "lib"
			target:       "github:numtide/flake-utils"
			id:           "flake-utils"
			description:  "Flake utility functions for multi-system support"
			versionRange: "latest"
		},
		{
			kind:         "service"
			target:       "path:../dir-cue"
			id:           "governance"
			description:  "Governance system for contract schema and validation"
			optional:     false
		},
		{
			kind:         "lib"
			target:       "github:cachix/pre-commit-hooks.nix"
			id:           "pre-commit-hooks"
			description:  "Pre-commit hooks for code quality enforcement"
			versionRange: "latest"
		}
	]
}