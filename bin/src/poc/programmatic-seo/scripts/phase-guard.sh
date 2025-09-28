#!/bin/bash

# Phase Guard Validation Script
# Ensures safe phase progression and deletion safety

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"
RECEIPTS_DIR="$DOCS_DIR/.receipts"
STATUS_FILE="$DOCS_DIR/PHASES_STATUS.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validate that required files exist
check_prerequisites() {
	if [[ ! -f "$STATUS_FILE" ]]; then
		log_error "Status file missing: $STATUS_FILE"
		return 1
	fi

	if [[ ! -d "$RECEIPTS_DIR" ]]; then
		log_error "Receipts directory missing: $RECEIPTS_DIR"
		return 1
	fi

	if ! command -v jq >/dev/null 2>&1; then
		log_error "jq is required but not installed"
		return 1
	fi

	return 0
}

# Validate a specific phase
validate_phase() {
	local phase="$1"
	local phase_file_pattern="$DOCS_DIR/phases/${phase}-*.md"
	local receipt_file="$RECEIPTS_DIR/${phase}.done"

	log_info "Validating phase $phase..."

	# Check if phase file exists
	local phase_files=(${phase_file_pattern})
	local phase_file_exists=false

	for file in "${phase_files[@]}"; do
		if [[ -f "$file" ]]; then
			phase_file_exists=true
			log_info "Phase file exists: $(basename "$file")"
			break
		fi
	done

	if [[ "$phase_file_exists" == "true" ]]; then
		log_info "Phase $phase appears to be in progress"

		# Check if phase status matches
		local status=$(jq -r ".phases.\"$phase\".status // \"unknown\"" "$STATUS_FILE")
		if [[ "$status" == "completed" ]]; then
			log_warn "Phase file exists but status is 'completed' - possible inconsistency"
			return 2
		fi

		return 0
	fi

	# Phase file missing - validate completion
	log_info "Phase file missing, checking completion validation..."

	# Check receipt file exists
	if [[ ! -f "$receipt_file" ]]; then
		log_error "Phase file deleted without proper receipt: $receipt_file"
		return 1
	fi

	# Validate receipt JSON format
	if ! jq . "$receipt_file" >/dev/null 2>&1; then
		log_error "Receipt file contains invalid JSON: $receipt_file"
		return 1
	fi

	# Check phase status in status file
	local status=$(jq -r ".phases.\"$phase\".status // \"unknown\"" "$STATUS_FILE")
	if [[ "$status" != "completed" ]]; then
		log_error "Phase status is '$status', expected 'completed' for deleted phase"
		return 1
	fi

	# Validate all gates are true in receipt
	local implementation_gates_false=$(jq -r '.gates.implementation_checklist // {} | to_entries[] | select(.value == false) | .key' "$receipt_file" | wc -l)
	local acceptance_gates_false=$(jq -r '.gates.acceptance_criteria // {} | to_entries[] | select(.value == false) | .key' "$receipt_file" | wc -l)

	if [[ $implementation_gates_false -gt 0 ]]; then
		log_error "Implementation checklist contains false values: $implementation_gates_false items"
		return 1
	fi

	if [[ $acceptance_gates_false -gt 0 ]]; then
		log_error "Acceptance criteria contains false values: $acceptance_gates_false items"
		return 1
	fi

	# Check commit hash exists
	local commit_hash=$(jq -r '.completion.commit_hash // "null"' "$receipt_file")
	if [[ "$commit_hash" == "null" || "$commit_hash" == "placeholder-commit-hash" ]]; then
		log_error "Receipt contains placeholder or missing commit hash"
		return 1
	fi

	# Verify commit exists in git history (if we're in a git repo)
	if git rev-parse --git-dir >/dev/null 2>&1; then
		if ! git cat-file -e "$commit_hash" >/dev/null 2>&1; then
			log_error "Commit hash $commit_hash does not exist in git history"
			return 1
		fi
	fi

	log_info "Phase $phase validation passed - properly completed and deleted"
	return 0
}

# Check all phases
check_all() {
	log_info "Checking all phases..."

	local all_passed=true
	local phases=$(jq -r '.phases | keys[]' "$STATUS_FILE")

	for phase in $phases; do
		if ! validate_phase "$phase"; then
			all_passed=false
		fi
		echo # Empty line for readability
	done

	if [[ "$all_passed" == "true" ]]; then
		log_info "All phase validations passed"
		return 0
	else
		log_error "Some phase validations failed"
		return 1
	fi
}

# Prepare phase for deletion
prepare_delete() {
	local phase="$1"
	local phase_file_pattern="$DOCS_DIR/phases/${phase}-*.md"
	local receipt_file="$RECEIPTS_DIR/${phase}.done"
	local backup_dir="$RECEIPTS_DIR/backups"

	log_info "Preparing phase $phase for deletion..."

	# Find phase file
	local phase_files=(${phase_file_pattern})
	local phase_file=""

	for file in "${phase_files[@]}"; do
		if [[ -f "$file" ]]; then
			phase_file="$file"
			break
		fi
	done

	if [[ -z "$phase_file" ]]; then
		log_error "No phase file found for phase $phase"
		return 1
	fi

	# Validate receipt exists and is complete
	if [[ ! -f "$receipt_file" ]]; then
		log_error "Receipt file missing: $receipt_file"
		log_error "Cannot delete phase file without valid completion receipt"
		return 1
	fi

	# Run validation
	if ! validate_phase "$phase"; then
		log_error "Phase validation failed - cannot prepare for deletion"
		return 1
	fi

	# Create backup directory if it doesn't exist
	mkdir -p "$backup_dir"

	# Create backup with timestamp
	local timestamp=$(date +%Y%m%d_%H%M%S)
	local backup_file="$backup_dir/$(basename "$phase_file").$timestamp"

	cp "$phase_file" "$backup_file"
	log_info "Backup created: $backup_file"

	log_info "Phase $phase is ready for deletion"
	log_info "To delete: rm \"$phase_file\""
	log_info "Backup available at: $backup_file"

	return 0
}

# Generate status report
status_report() {
	log_info "Phase Status Report"
	echo "===================="

	local phases=$(jq -r '.phases | keys[]' "$STATUS_FILE")

	for phase in $phases; do
		local title=$(jq -r ".phases.\"$phase\".title" "$STATUS_FILE")
		local status=$(jq -r ".phases.\"$phase\".status" "$STATUS_FILE")
		local completion_date=$(jq -r ".phases.\"$phase\".completion_date // \"N/A\"" "$STATUS_FILE")

		echo "Phase $phase: $title"
		echo "  Status: $status"
		echo "  Completion: $completion_date"
		echo
	done
}

# Main function
main() {
	if ! check_prerequisites; then
		exit 1
	fi

	case "${1:-}" in
	"validate")
		if [[ -z "${2:-}" ]]; then
			log_error "Usage: $0 validate <phase>"
			exit 1
		fi
		validate_phase "$2"
		;;
	"check-all")
		check_all
		;;
	"prepare-delete")
		if [[ -z "${2:-}" ]]; then
			log_error "Usage: $0 prepare-delete <phase>"
			exit 1
		fi
		prepare_delete "$2"
		;;
	"status")
		status_report
		;;
	*)
		echo "Usage: $0 {validate|check-all|prepare-delete|status} [phase]"
		echo
		echo "Commands:"
		echo "  validate <phase>     - Validate specific phase"
		echo "  check-all           - Check all phases"
		echo "  prepare-delete <phase> - Prepare phase for safe deletion"
		echo "  status              - Show phase status report"
		exit 1
		;;
	esac
}

main "$@"
