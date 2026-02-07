#!/bin/bash
# Vibe.d Development Helper Script
# Usage: ./scripts/dev.sh [command]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Commands
cmd_build() {
    local compiler="${1:-dmd}"
    local build_type="${2:-debug}"
    print_header "Building with $compiler ($build_type)"
    dub build --compiler="$compiler" --build="$build_type"
    print_success "Build complete"
}

cmd_run() {
    local compiler="${1:-dmd}"
    print_header "Running with $compiler"
    dub run --compiler="$compiler"
}

cmd_test() {
    local compiler="${1:-dmd}"
    print_header "Running tests with $compiler"
    dub test --compiler="$compiler"
    print_success "Tests complete"
}

cmd_docker_up() {
    print_header "Starting Docker services"
    docker-compose up -d
    print_success "Services started"
    docker-compose ps
}

cmd_docker_down() {
    print_header "Stopping Docker services"
    docker-compose down
    print_success "Services stopped"
}

cmd_docker_logs() {
    local service="${1:-app}"
    docker-compose logs -f "$service"
}

cmd_docker_build() {
    print_header "Building Docker images"
    docker-compose build --no-cache
    print_success "Images built"
}

cmd_clean() {
    print_header "Cleaning build artifacts"
    rm -rf .dub
    rm -f app app-test-library
    dub clean
    print_success "Clean complete"
}

cmd_format() {
    print_header "Formatting code"
    dub run dfmt -- -i source/
    print_success "Formatting complete"
}

cmd_lint() {
    print_header "Running linter"
    dub run dscanner -- --styleCheck source/
}

cmd_deps() {
    print_header "Fetching dependencies"
    dub fetch
    print_success "Dependencies fetched"
}

cmd_help() {
    echo "Vibe.d Development Helper Script"
    echo ""
    echo "Usage: ./scripts/dev.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build [compiler] [type]  Build the project (default: dmd debug)"
    echo "  run [compiler]           Run the project (default: dmd)"
    echo "  test [compiler]          Run tests (default: dmd)"
    echo "  docker-up                Start Docker services"
    echo "  docker-down              Stop Docker services"
    echo "  docker-logs [service]    View service logs (default: app)"
    echo "  docker-build             Rebuild Docker images"
    echo "  clean                    Clean build artifacts"
    echo "  format                   Format source code"
    echo "  lint                     Run static analysis"
    echo "  deps                     Fetch dependencies"
    echo "  help                     Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/dev.sh build ldc2 release"
    echo "  ./scripts/dev.sh docker-logs db"
}

# Main
cd "$PROJECT_DIR"

case "${1:-help}" in
    build)
        cmd_build "$2" "$3"
        ;;
    run)
        cmd_run "$2"
        ;;
    test)
        cmd_test "$2"
        ;;
    docker-up)
        cmd_docker_up
        ;;
    docker-down)
        cmd_docker_down
        ;;
    docker-logs)
        cmd_docker_logs "$2"
        ;;
    docker-build)
        cmd_docker_build
        ;;
    clean)
        cmd_clean
        ;;
    format)
        cmd_format
        ;;
    lint)
        cmd_lint
        ;;
    deps)
        cmd_deps
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
