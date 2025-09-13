#!/bin/bash

# DeCoin Services Shutdown Script
# Gracefully stops all DeCoin services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} ✓ $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')]${NC} ⚠ $1"
}

print_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')]${NC} ✗ $1"
}

# Function to check if services are running
check_running_services() {
    if docker-compose ps -q 2>/dev/null | grep -q .; then
        return 0
    elif docker compose ps -q 2>/dev/null | grep -q .; then
        return 0
    else
        return 1
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping DeCoin services..."

    if docker-compose down 2>/dev/null; then
        print_success "Services stopped with docker-compose"
    elif docker compose down 2>/dev/null; then
        print_success "Services stopped with docker compose"
    else
        print_warning "No services were running or failed to stop"
        return 1
    fi
}

# Function to remove volumes
remove_volumes() {
    read -p "Remove data volumes as well? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing volumes..."
        if docker-compose down -v 2>/dev/null; then
            print_success "Volumes removed with docker-compose"
        elif docker compose down -v 2>/dev/null; then
            print_success "Volumes removed with docker compose"
        else
            print_warning "Failed to remove volumes"
        fi
    fi
}

# Function to clean up Docker system
cleanup_docker() {
    read -p "Clean up unused Docker resources? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up Docker system..."
        docker system prune -f
        print_success "Docker cleanup complete"
    fi
}

# Main execution
main() {
    echo "╔════════════════════════════════════════╗"
    echo "║    DeCoin Services Shutdown Script     ║"
    echo "╚════════════════════════════════════════╝"
    echo

    # Change to script directory
    cd "$(dirname "$0")"

    # Check if services are running
    if check_running_services; then
        print_status "Found running DeCoin services"

        # Show current status
        echo
        print_status "Current container status:"
        docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null
        echo

        # Stop services
        stop_services

        # Optional cleanup
        remove_volumes
        cleanup_docker

        echo
        print_success "DeCoin services have been stopped"
    else
        print_warning "No DeCoin services are currently running"
    fi

    echo
    echo "To start services again, run: ./start-services.sh"
}

# Handle script interruption
trap 'print_warning "Script interrupted by user"; exit 130' INT TERM

# Run main function
main "$@"