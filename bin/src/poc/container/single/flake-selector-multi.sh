#!/usr/bin/env bash
set -euo pipefail

# Dynamic Flake Multi-Container Selector
# Allows selection and building of multiple containers from a single flake

# Container definitions with descriptions
declare -A CONTAINERS=(
    ["1"]="container-base"
    ["2"]="container-nodejs" 
    ["3"]="container-python"
    ["4"]="container-go"
    ["5"]="container-integrated"
)

declare -A DESCRIPTIONS=(
    ["container-base"]="Base container with essential tools"
    ["container-nodejs"]="Node.js runtime container with npm support"
    ["container-python"]="Python runtime container with pip support"
    ["container-go"]="Go runtime container with build tools"
    ["container-integrated"]="Integrated container with external flakes"
)

# Global variables
SELECTED_CONTAINERS=()
NON_INTERACTIVE=false
BATCH_MODE=false
BATCH_INPUT=""

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Dynamic Flake Multi-Container Selector

OPTIONS:
    --list              List available containers
    --describe          Show container descriptions
    --help              Show this help message
    --non-interactive   Run in non-interactive mode
    --list-selected     List selected containers and exit
    --summary           Show selection summary
    --batch SELECTION   Run in batch mode with predefined selection
                       Format: "1,2,3" or "1-3" for ranges

EXAMPLES:
    $0                          # Interactive mode
    $0 --list                   # List all containers
    $0 --batch "1,2"           # Select base and nodejs containers
    $0 --batch "1-3"           # Select containers 1 through 3

INTERACTIVE USAGE:
    - Enter container numbers separated by commas: 1,2,3
    - Enter ranges: 1-3 (expands to 1,2,3)
    - Type 'done' to finish selection
    - Type 'build' to build selected containers
    - Type 'preview' to show run commands

EOF
}

list_containers() {
    echo "Available containers:"
    for num in $(seq 1 ${#CONTAINERS[@]}); do
        container=${CONTAINERS[$num]}
        description=${DESCRIPTIONS[$container]}
        printf "%s%d%s) %s - %s\n" "$BLUE" "$num" "$NC" "$container" "$description"
    done
}

describe_containers() {
    echo "Container Descriptions:"
    echo "======================"
    for num in $(seq 1 ${#CONTAINERS[@]}); do
        container=${CONTAINERS[$num]}
        description=${DESCRIPTIONS[$container]}
        printf "\n%s%s%s:\n" "$GREEN" "$container" "$NC"
        printf "  %s\n" "$description"
        printf "  Build: nix build .#%s\n" "$container"
        printf "  Run: podman run --rm localhost/%s:latest\n" "${container/-container/}-container"
    done
}

validate_number() {
    local num="$1"
    if [[ ! "$num" =~ ^[0-9]+$ ]] || [ "$num" -lt 1 ] || [ "$num" -gt ${#CONTAINERS[@]} ]; then
        return 1
    fi
    return 0
}

expand_range() {
    local range="$1"
    if [[ "$range" =~ ^[0-9]+-[0-9]+$ ]]; then
        local start=$(echo "$range" | cut -d'-' -f1)
        local end=$(echo "$range" | cut -d'-' -f2)
        
        if ! validate_number "$start" || ! validate_number "$end"; then
            echo "Invalid range: $range" >&2
            return 1
        fi
        
        if [ "$start" -gt "$end" ]; then
            echo "Invalid range: start must be <= end" >&2
            return 1
        fi
        
        seq "$start" "$end" | tr '\n' ',' | sed 's/,$//'
    else
        echo "$range"
    fi
}

parse_selection() {
    local input="$1"
    local numbers=()
    
    # Handle ranges and comma-separated values
    IFS=',' read -ra PARTS <<< "$input"
    for part in "${PARTS[@]}"; do
        part=$(echo "$part" | xargs) # trim whitespace
        if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
            # It's a range
            local expanded
            expanded=$(expand_range "$part")
            if [ $? -ne 0 ]; then
                return 1
            fi
            IFS=',' read -ra RANGE_NUMS <<< "$expanded"
            numbers+=("${RANGE_NUMS[@]}")
        else
            # It's a single number
            if ! validate_number "$part"; then
                echo "Invalid container number: $part" >&2
                return 1
            fi
            numbers+=("$part")
        fi
    done
    
    # Remove duplicates and sort
    printf '%s\n' "${numbers[@]}" | sort -nu | tr '\n' ' '
}

add_to_selection() {
    local input="$1"
    local parsed_nums
    parsed_nums=$(parse_selection "$input")
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    for num in $parsed_nums; do
        container=${CONTAINERS[$num]}
        if [[ ! " ${SELECTED_CONTAINERS[*]} " =~ " $container " ]]; then
            SELECTED_CONTAINERS+=("$container")
        fi
    done
}

show_selected() {
    if [ ${#SELECTED_CONTAINERS[@]} -eq 0 ]; then
        echo "No containers selected."
        return
    fi
    
    echo "Selected containers:"
    for i in "${!SELECTED_CONTAINERS[@]}"; do
        local container="${SELECTED_CONTAINERS[$i]}"
        printf "%s%d%s) %s - %s\n" "$GREEN" $((i+1)) "$NC" "$container" "${DESCRIPTIONS[$container]}"
    done
}

show_summary() {
    echo "Selection Summary:"
    echo "=================="
    echo "Selected containers: ${#SELECTED_CONTAINERS[@]}"
    if [ ${#SELECTED_CONTAINERS[@]} -gt 0 ]; then
        for container in "${SELECTED_CONTAINERS[@]}"; do
            echo "  - $container"
        done
    fi
}

build_containers() {
    if [ ${#SELECTED_CONTAINERS[@]} -eq 0 ]; then
        echo "${RED}No containers selected for building${NC}" >&2
        return 1
    fi
    
    echo "Building selected containers..."
    for container in "${SELECTED_CONTAINERS[@]}"; do
        echo "${YELLOW}Building $container...${NC}"
        if nix build ".#$container"; then
            echo "${GREEN}✓ $container built successfully${NC}"
        else
            echo "${RED}✗ Failed to build $container${NC}" >&2
            return 1
        fi
    done
}

show_preview() {
    if [ ${#SELECTED_CONTAINERS[@]} -eq 0 ]; then
        echo "${RED}No containers selected for preview${NC}" >&2
        return 1
    fi
    
    echo "Container Run Commands Preview:"
    echo "==============================="
    for container in "${SELECTED_CONTAINERS[@]}"; do
        local image_name="${container/-container/}-container"
        echo "# $container"
        echo "gunzip -c \$(nix build .#$container --print-out-paths) | podman load"
        echo "podman run --rm localhost/$image_name:latest"
        echo ""
    done
}

interactive_mode() {
    echo "=== Dynamic Flake Multi-Container Selector ==="
    echo ""
    list_containers
    echo ""
    echo "Instructions:"
    echo "- Enter container numbers (comma-separated): 1,2,3"
    echo "- Enter ranges: 1-3"  
    echo "- Commands: 'build', 'preview', 'summary', 'done'"
    echo ""
    
    while true; do
        if [ ${#SELECTED_CONTAINERS[@]} -gt 0 ]; then
            echo "Currently selected: ${SELECTED_CONTAINERS[*]}"
        fi
        
        echo -n "Enter selection or command: "
        read -r input
        
        case "$input" in
            "done"|"exit"|"quit")
                break
                ;;
            "build")
                build_containers
                ;;
            "preview")
                show_preview
                ;;
            "summary")
                show_summary
                ;;
            "help")
                show_help
                ;;
            "list")
                list_containers
                ;;
            "clear")
                SELECTED_CONTAINERS=()
                echo "Selection cleared."
                ;;
            "")
                continue
                ;;
            *)
                if add_to_selection "$input"; then
                    echo "${GREEN}Added to selection${NC}"
                else
                    echo "${RED}Invalid input. Try again.${NC}" >&2
                fi
                ;;
        esac
    done
}

non_interactive_mode() {
    local input
    read -r input
    
    if ! add_to_selection "$input"; then
        echo "Invalid selection" >&2
        exit 1
    fi
    
    # Check for additional commands
    while read -r cmd 2>/dev/null; do
        case "$cmd" in
            "build")
                build_containers
                exit $?
                ;;
            "preview")
                show_preview
                exit 0
                ;;
            "done"|"")
                break
                ;;
        esac
    done
}

batch_mode() {
    if ! add_to_selection "$BATCH_INPUT"; then
        echo "Invalid batch input: $BATCH_INPUT" >&2
        exit 1
    fi
    
    show_selected
}

# Main execution
main() {
    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --list)
                list_containers
                exit 0
                ;;
            --describe)
                describe_containers
                exit 0
                ;;
            --non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            --list-selected)
                NON_INTERACTIVE=true
                non_interactive_mode
                show_selected
                exit 0
                ;;
            --summary)
                NON_INTERACTIVE=true
                non_interactive_mode
                show_summary
                exit 0
                ;;
            --batch)
                if [ $# -lt 2 ]; then
                    echo "Error: --batch requires an argument" >&2
                    exit 1
                fi
                BATCH_MODE=true
                BATCH_INPUT="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                show_help >&2
                exit 1
                ;;
        esac
    done
    
    # Execute based on mode
    if [ "$BATCH_MODE" = true ]; then
        batch_mode
    elif [ "$NON_INTERACTIVE" = true ]; then
        non_interactive_mode
        show_selected
    else
        interactive_mode
        if [ ${#SELECTED_CONTAINERS[@]} -gt 0 ]; then
            echo ""
            show_summary
        fi
    fi
}

# Run main function
main "$@"