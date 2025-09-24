#!/usr/bin/env bash
# Environment-specific secret validation script
# Validates R2 configuration files for security and correctness

set -euo pipefail

# Configuration
SECRETS_DIR="./secrets/r2"
SCHEMA_DIR="./schemas"
ENVIRONMENTS=("dev" "stg" "prod")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are available
check_dependencies() {
    local deps=("sops" "yq")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Install with: nix profile install nixpkgs#sops nixpkgs#yq"
        exit 1
    fi
}

# Validate SOPS configuration
validate_sops_config() {
    log_info "Validating SOPS configuration..."

    if [ ! -f ".sops.yaml" ]; then
        log_error "SOPS configuration file not found: .sops.yaml"
        return 1
    fi

    # Check if Age key is configured
    if grep -q "YOUR_AGE_PUBLIC_KEY_WILL_BE_INSERTED_HERE" .sops.yaml; then
        log_error "SOPS Age key not configured. Run 'nix run .#secrets-init' first"
        return 1
    fi

    # Validate environment-specific rules exist
    local env_rules_found=false
    for env in "${ENVIRONMENTS[@]}"; do
        if grep -q "secrets/r2/${env}\.yaml" .sops.yaml; then
            env_rules_found=true
            break
        fi
    done

    if [ "$env_rules_found" = false ]; then
        log_error "Environment-specific SOPS rules not found in .sops.yaml"
        return 1
    fi

    log_success "SOPS configuration is valid"
    return 0
}

# Validate environment secret file
validate_environment_file() {
    local env="$1"
    local secret_file="${SECRETS_DIR}/${env}.yaml"
    local template_file="${SECRETS_DIR}/${env}.yaml.template"
    local errors=0

    log_info "Validating environment: $env"

    # Check if template exists
    if [ ! -f "$template_file" ]; then
        log_error "Template file not found: $template_file"
        ((errors++))
    fi

    # Check if secret file exists
    if [ ! -f "$secret_file" ]; then
        log_warning "Secret file not found: $secret_file"
        log_info "Create it by copying from template: cp $template_file $secret_file"
        return 0  # Not an error, just missing
    fi

    # Validate file can be decrypted
    log_info "Testing SOPS decryption for $env..."
    if ! sops --decrypt "$secret_file" > /dev/null 2>&1; then
        log_error "Failed to decrypt $secret_file with SOPS"
        ((errors++))
    else
        log_success "SOPS decryption successful for $env"
    fi

    # Validate YAML structure
    log_info "Validating YAML structure for $env..."
    local decrypted_content
    if decrypted_content=$(sops --decrypt "$secret_file" 2>/dev/null); then
        validate_yaml_structure "$env" "$decrypted_content"
        local yaml_result=$?
        ((errors += yaml_result))
    else
        log_error "Cannot decrypt file for YAML validation"
        ((errors++))
    fi

    if [ $errors -eq 0 ]; then
        log_success "Environment $env validation passed"
    else
        log_error "Environment $env validation failed with $errors errors"
    fi

    return $errors
}

# Validate YAML structure and required fields
validate_yaml_structure() {
    local env="$1"
    local content="$2"
    local errors=0

    # Required fields for all environments
    local required_fields=(
        "environment"
        "cf_account_id"
        "r2_buckets"
        "r2_s3_endpoint"
        "r2_region"
        "security"
    )

    log_info "Checking required fields for $env..."

    # Check environment matches
    local env_value
    env_value=$(echo "$content" | yq eval '.environment' -)
    if [ "$env_value" != "$env" ]; then
        log_error "Environment mismatch: expected '$env', got '$env_value'"
        ((errors++))
    fi

    # Check required fields exist
    for field in "${required_fields[@]}"; do
        local value
        value=$(echo "$content" | yq eval ".$field" -)
        if [ "$value" = "null" ] || [ "$value" = "" ]; then
            log_error "Missing required field: $field"
            ((errors++))
        fi
    done

    # Validate Cloudflare Account ID format
    local cf_account_id
    cf_account_id=$(echo "$content" | yq eval '.cf_account_id' -)
    if [[ ! "$cf_account_id" =~ ^[a-f0-9]{32}$ ]]; then
        log_error "Invalid Cloudflare Account ID format: $cf_account_id"
        ((errors++))
    fi

    # Validate R2 region is 'auto'
    local r2_region
    r2_region=$(echo "$content" | yq eval '.r2_region' -)
    if [ "$r2_region" != "auto" ]; then
        log_error "R2 region must be 'auto', got: $r2_region"
        ((errors++))
    fi

    # Validate R2 endpoint contains account ID
    local r2_endpoint
    r2_endpoint=$(echo "$content" | yq eval '.r2_s3_endpoint' -)
    if [[ ! "$r2_endpoint" =~ $cf_account_id ]]; then
        log_error "R2 S3 endpoint must contain account ID"
        ((errors++))
    fi

    # Validate buckets array
    local bucket_count
    bucket_count=$(echo "$content" | yq eval '.r2_buckets | length' -)
    if [ "$bucket_count" = "0" ] || [ "$bucket_count" = "null" ]; then
        log_error "At least one R2 bucket must be configured"
        ((errors++))
    fi

    # Validate individual buckets
    log_info "Validating bucket configurations..."
    local i=0
    while [ $i -lt "$bucket_count" ]; do
        local bucket_name bucket_purpose bucket_public
        bucket_name=$(echo "$content" | yq eval ".r2_buckets[$i].name" -)
        bucket_purpose=$(echo "$content" | yq eval ".r2_buckets[$i].purpose" -)
        bucket_public=$(echo "$content" | yq eval ".r2_buckets[$i].public_access" -)

        if [ "$bucket_name" = "null" ] || [ "$bucket_name" = "" ]; then
            log_error "Bucket $i: missing name"
            ((errors++))
        fi

        if [ "$bucket_purpose" = "null" ] || [ "$bucket_purpose" = "" ]; then
            log_error "Bucket $i: missing purpose"
            ((errors++))
        fi

        if [ "$bucket_public" != "true" ] && [ "$bucket_public" != "false" ]; then
            log_error "Bucket $i: public_access must be boolean"
            ((errors++))
        fi

        ((i++))
    done

    # Environment-specific validations
    case "$env" in
        "prod")
            validate_production_requirements "$content"
            ((errors += $?))
            ;;
        "dev")
            validate_development_requirements "$content"
            ((errors += $?))
            ;;
        "stg")
            validate_staging_requirements "$content"
            ((errors += $?))
            ;;
    esac

    return $errors
}

# Validate production-specific requirements
validate_production_requirements() {
    local content="$1"
    local errors=0

    log_info "Validating production-specific requirements..."

    # Check security settings
    local require_auth rate_limiting encryption_at_rest
    require_auth=$(echo "$content" | yq eval '.security.require_auth' -)
    rate_limiting=$(echo "$content" | yq eval '.security.rate_limiting' -)
    encryption_at_rest=$(echo "$content" | yq eval '.security.encryption_at_rest' -)

    if [ "$require_auth" != "true" ]; then
        log_error "Production must require authentication"
        ((errors++))
    fi

    if [ "$rate_limiting" != "true" ]; then
        log_error "Production must enable rate limiting"
        ((errors++))
    fi

    if [ "$encryption_at_rest" != "true" ]; then
        log_error "Production should enable encryption at rest"
        ((errors++))
    fi

    # Check monitoring is enabled
    local enable_metrics
    enable_metrics=$(echo "$content" | yq eval '.monitoring.enable_metrics' -)
    if [ "$enable_metrics" != "true" ]; then
        log_warning "Production should enable metrics monitoring"
    fi

    return $errors
}

# Validate development-specific requirements
validate_development_requirements() {
    local content="$1"
    local errors=0

    log_info "Validating development-specific requirements..."

    # Check CORS origins include localhost
    local cors_origins
    cors_origins=$(echo "$content" | yq eval '.development.cors_origins[]' - 2>/dev/null | grep -c "localhost" || echo "0")
    if [ "$cors_origins" -eq 0 ]; then
        log_warning "Development should include localhost in CORS origins"
    fi

    return $errors
}

# Validate staging-specific requirements
validate_staging_requirements() {
    local content="$1"
    local errors=0

    log_info "Validating staging-specific requirements..."

    # Check test mode is enabled
    local test_mode
    test_mode=$(echo "$content" | yq eval '.testing.enable_test_mode' -)
    if [ "$test_mode" != "true" ]; then
        log_warning "Staging should enable test mode"
    fi

    return $errors
}

# Check for template placeholders in secret files
check_for_placeholders() {
    local env="$1"
    local secret_file="${SECRETS_DIR}/${env}.yaml"
    local errors=0

    if [ ! -f "$secret_file" ]; then
        return 0  # Skip if file doesn't exist
    fi

    log_info "Checking for template placeholders in $env..."

    local placeholders=(
        "your-.*-account-id-here"
        "your-.*-access-key-here"
        "your-.*-secret-key-here"
        "YYYY-MM-DD"
        "yourdomain.com"
    )

    local decrypted_content
    if decrypted_content=$(sops --decrypt "$secret_file" 2>/dev/null); then
        for placeholder in "${placeholders[@]}"; do
            if echo "$decrypted_content" | grep -q "$placeholder"; then
                log_error "Found template placeholder '$placeholder' in $secret_file"
                ((errors++))
            fi
        done
    fi

    return $errors
}

# Generate validation report
generate_report() {
    local total_errors=0
    local validated_envs=0

    log_info "=== Environment Secrets Validation Report ==="

    # Check dependencies
    check_dependencies

    # Validate SOPS configuration
    validate_sops_config
    local sops_result=$?
    ((total_errors += sops_result))

    # Validate each environment
    for env in "${ENVIRONMENTS[@]}"; do
        echo
        validate_environment_file "$env"
        local env_result=$?
        ((total_errors += env_result))

        check_for_placeholders "$env"
        local placeholder_result=$?
        ((total_errors += placeholder_result))

        if [ $env_result -eq 0 ] && [ $placeholder_result -eq 0 ]; then
            ((validated_envs++))
        fi
    done

    echo
    log_info "=== Validation Summary ==="
    log_info "Environments validated: $validated_envs/${#ENVIRONMENTS[@]}"

    if [ $total_errors -eq 0 ]; then
        log_success "All validations passed!"
        return 0
    else
        log_error "Validation failed with $total_errors total errors"
        return 1
    fi
}

# Main execution
main() {
    local command="${1:-validate}"

    case "$command" in
        "validate"|"")
            generate_report
            ;;
        "check-env")
            if [ -z "${2:-}" ]; then
                log_error "Usage: $0 check-env <environment>"
                exit 1
            fi
            validate_environment_file "$2"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command] [options]"
            echo
            echo "Commands:"
            echo "  validate     Run full validation (default)"
            echo "  check-env    Validate specific environment"
            echo "  help         Show this help"
            echo
            echo "Examples:"
            echo "  $0                    # Run full validation"
            echo "  $0 check-env dev     # Validate dev environment only"
            ;;
        *)
            log_error "Unknown command: $command"
            log_info "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"