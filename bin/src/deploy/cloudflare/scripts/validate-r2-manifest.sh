#!/bin/bash
set -euo pipefail

# R2 Connection Manifest Validation Script
# Validates R2 manifest files against basic structure and constraints

validate_manifest() {
    local file="$1"
    local errors=0

    echo "Validating $file..."

    # Check JSON syntax
    if ! jq empty < "$file" 2>/dev/null; then
        echo "  ✗ Invalid JSON syntax"
        return 1
    fi
    echo "  ✓ Valid JSON syntax"

    # Check required top-level fields
    required_fields=("account_id" "endpoint" "region" "buckets" "connection_mode" "meta")
    for field in "${required_fields[@]}"; do
        if jq --exit-status "has(\"$field\")" < "$file" > /dev/null 2>&1; then
            echo "  ✓ Has $field"
        else
            echo "  ✗ Missing required field: $field"
            ((errors++))
        fi
    done

    # Check meta structure
    if jq --exit-status '.meta | has("environment") and has("version") and has("created_at")' < "$file" > /dev/null 2>&1; then
        echo "  ✓ Meta object has required fields"
    else
        echo "  ✗ Meta object missing required fields (environment, version, created_at)"
        ((errors++))
    fi

    # Check buckets array
    if jq --exit-status '.buckets | type == "array" and length > 0' < "$file" > /dev/null 2>&1; then
        bucket_count=$(jq '.buckets | length' < "$file")
        echo "  ✓ Buckets is non-empty array with $bucket_count buckets"

        # Check bucket structure
        if jq --exit-status '.buckets[] | has("name")' < "$file" > /dev/null 2>&1; then
            echo "  ✓ All buckets have name field"
        else
            echo "  ✗ Some buckets missing name field"
            ((errors++))
        fi
    else
        echo "  ✗ Buckets must be a non-empty array"
        ((errors++))
    fi

    # Validate connection mode
    connection_mode=$(jq -r '.connection_mode' < "$file")
    if [[ "$connection_mode" =~ ^(workers-binding|s3-api|hybrid)$ ]]; then
        echo "  ✓ Connection mode '$connection_mode' is valid"
    else
        echo "  ✗ Invalid connection mode: $connection_mode (must be workers-binding, s3-api, or hybrid)"
        ((errors++))
    fi

    # Validate region
    region=$(jq -r '.region' < "$file")
    if [[ "$region" =~ ^(auto|eeur|enam|apac|weur|wnam)$ ]]; then
        echo "  ✓ Region '$region' is valid"
    else
        echo "  ✗ Invalid region: $region (must be auto, eeur, enam, apac, weur, or wnam)"
        ((errors++))
    fi

    # Validate version format
    version=$(jq -r '.meta.version' < "$file")
    if [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "  ✓ Version '$version' follows semantic versioning"
    else
        echo "  ✗ Version '$version' must follow semantic versioning (x.y.z)"
        ((errors++))
    fi

    # Validate endpoint format
    endpoint=$(jq -r '.endpoint' < "$file")
    if [[ "$endpoint" =~ ^https://.*\.r2\.cloudflarestorage\.com$ ]]; then
        echo "  ✓ Endpoint follows R2 format"
    else
        echo "  ✗ Endpoint must follow format: https://{account_id}.r2.cloudflarestorage.com"
        ((errors++))
    fi

    # Validate credentials based on connection mode
    if [[ "$connection_mode" == "s3-api" || "$connection_mode" == "hybrid" ]]; then
        if jq --exit-status '.credentials != null and .credentials | has("access_key_id") and has("secret_access_key")' < "$file" > /dev/null 2>&1; then
            echo "  ✓ Credentials present and valid for $connection_mode mode"
        else
            echo "  ✗ Credentials with access_key_id and secret_access_key required for $connection_mode mode"
            ((errors++))
        fi
    else
        echo "  ✓ No credentials required for $connection_mode mode"
    fi

    # Validate bucket names
    while IFS= read -r bucket_name; do
        if [[ ${#bucket_name} -ge 3 && ${#bucket_name} -le 63 && "$bucket_name" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ && ! "$bucket_name" =~ \.\. && ! "$bucket_name" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "  ✓ Bucket name '$bucket_name' is valid"
        else
            echo "  ✗ Invalid bucket name '$bucket_name' (must follow S3 naming rules)"
            ((errors++))
        fi
    done < <(jq -r '.buckets[].name' < "$file")

    if [ $errors -eq 0 ]; then
        echo "  ✅ $file validation passed"
        return 0
    else
        echo "  ❌ $file validation failed with $errors errors"
        return 1
    fi
}

main() {
    if [ $# -eq 0 ]; then
        echo "Usage: $0 <manifest-file> [manifest-file2] ..."
        echo ""
        echo "Examples:"
        echo "  $0 examples/r2.dev.json.example"
        echo "  $0 out/r2.dev.json out/r2.prod.json"
        exit 1
    fi

    local total_files=0
    local passed_files=0

    for file in "$@"; do
        if [ ! -f "$file" ]; then
            echo "Error: File not found: $file"
            continue
        fi

        ((total_files++))

        if validate_manifest "$file"; then
            ((passed_files++))
        fi
        echo ""
    done

    echo "Summary: $passed_files/$total_files files passed validation"

    if [ $passed_files -eq $total_files ]; then
        exit 0
    else
        exit 1
    fi
}

main "$@"