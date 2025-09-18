#!/bin/sh
# uri_parser.sh - URI parser with test cases

# URI parse function
parse_uri() {
    uri="$1"
    
    # Extract scheme
    scheme="${uri%%://*}"
    if [ "$scheme" = "$uri" ]; then
        scheme=""
    fi
    
    # Remove scheme://
    rest="${uri#*://}"
    if [ "$rest" = "$uri" ]; then
        rest="$uri"
    fi
    
    # Extract host
    host="${rest%%/*}"
    if [ "$host" = "$rest" ]; then
        # No path
        path=""
        temp="$rest"
    else
        # Has path
        path="/${rest#*/}"
        temp="$rest"
    fi
    
    # Extract fragment
    if echo "$path" | grep -q '#'; then
        fragment="${path#*#}"
        path="${path%%#*}"
    else
        fragment=""
    fi
    
    # Extract query
    if echo "$path" | grep -q '?'; then
        query="${path#*\?}"
        query="${query%%#*}"
        path="${path%%\?*}"
    else
        query=""
    fi
}

# Test function
test_uri() {
    uri="$1"
    expected_scheme="$2"
    expected_host="$3"
    expected_path="$4"
    expected_query="$5"
    expected_fragment="$6"
    
    parse_uri "$uri"
    
    echo "Testing: $uri"
    
    # Check results
    pass=1
    if [ "$scheme" != "$expected_scheme" ]; then
        echo "  ✗ scheme: got '$scheme', expected '$expected_scheme'"
        pass=0
    fi
    
    if [ "$host" != "$expected_host" ]; then
        echo "  ✗ host: got '$host', expected '$expected_host'"
        pass=0
    fi
    
    if [ "$path" != "$expected_path" ]; then
        echo "  ✗ path: got '$path', expected '$expected_path'"
        pass=0
    fi
    
    if [ "$query" != "$expected_query" ]; then
        echo "  ✗ query: got '$query', expected '$expected_query'"
        pass=0
    fi
    
    if [ "$fragment" != "$expected_fragment" ]; then
        echo "  ✗ fragment: got '$fragment', expected '$expected_fragment'"
        pass=0
    fi
    
    if [ $pass -eq 1 ]; then
        echo "  ✓ PASS"
    fi
    echo ""
}

# Run tests if script is executed directly
if [ "${0##*/}" = "uri_parser.sh" ]; then
    echo "=== URI Parser Test Suite ==="
    echo ""
    
    # Test cases
    test_uri "file:///home/user/file.txt" "file" "" "/home/user/file.txt" "" ""
    test_uri "s3://bucket/path/to/file.ts" "s3" "bucket" "/path/to/file.ts" "" ""
    test_uri "https://example.com/page" "https" "example.com" "/page" "" ""
    test_uri "https://example.com/page?foo=bar" "https" "example.com" "/page" "foo=bar" ""
    test_uri "https://example.com/page#section" "https" "example.com" "/page" "" "section"
    test_uri "https://example.com/page?foo=bar#section" "https" "example.com" "/page" "foo=bar" "section"
    test_uri "gs://my-bucket/dir/file.json" "gs" "my-bucket" "/dir/file.json" "" ""
    test_uri "http://localhost:8080/api/v1" "http" "localhost:8080" "/api/v1" "" ""
    test_uri "s3://bucket/file.ts#function" "s3" "bucket" "/file.ts" "" "function"
    test_uri "/local/path/file.txt" "" "" "/local/path/file.txt" "" ""
    
    # Usage example
    echo "=== Usage Example ==="
    parse_uri "s3://my-bucket/src/main.ts#parseFunction"
    echo "Parsed URI components:"
    echo "  scheme: $scheme"
    echo "  host: $host"
    echo "  path: $path"
    echo "  query: $query"
    echo "  fragment: $fragment"
fi

# Export function for sourcing
# Usage: . ./uri_parser.sh