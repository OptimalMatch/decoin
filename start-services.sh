#!/bin/bash

# DeCoin Services Startup Script
# Starts all DeCoin services with health checks and monitoring

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_WAIT_TIME=60  # Maximum seconds to wait for services
HEALTH_CHECK_INTERVAL=2  # Seconds between health checks

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

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        print_error "Docker Compose is not installed."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Function to check port availability
check_ports() {
    local ports=(11000 11080 11081 11082 11083)
    local all_clear=true

    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Port $port is already in use"
            all_clear=false
        fi
    done

    if [ "$all_clear" = false ]; then
        read -p "Some ports are in use. Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Exiting..."
            exit 1
        fi
    else
        print_success "All required ports are available"
    fi
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."

    if docker-compose build --quiet 2>/dev/null || docker compose build --quiet 2>/dev/null; then
        print_success "Docker images built successfully"
    else
        # Try without --quiet flag if it fails
        print_status "Building with verbose output..."
        docker-compose build || docker compose build
        print_success "Docker images built"
    fi
}

# Function to start services
start_services() {
    print_status "Starting DeCoin services..."

    # Stop any existing containers
    docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

    # Start services in detached mode
    if command -v docker-compose &> /dev/null; then
        if docker-compose up -d; then
            print_success "Services started with docker-compose"
        else
            print_error "Failed to start services with docker-compose"
            docker-compose logs --tail=20
            exit 1
        fi
    else
        if docker compose up -d; then
            print_success "Services started with docker compose"
        else
            print_error "Failed to start services with docker compose"
            docker compose logs --tail=20
            exit 1
        fi
    fi
}

# Function to wait for service health
wait_for_service() {
    local service_name=$1
    local port=$2
    local url="http://localhost:${port}/status"
    local elapsed=0

    print_status "Waiting for ${service_name} on port ${port}..."

    while [ $elapsed -lt $MAX_WAIT_TIME ]; do
        if curl -s -f -o /dev/null "$url" 2>/dev/null; then
            print_success "${service_name} is healthy"
            return 0
        fi

        sleep $HEALTH_CHECK_INTERVAL
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))
        echo -n "."
    done

    echo
    print_warning "${service_name} did not become healthy within ${MAX_WAIT_TIME} seconds"
    return 1
}

# Function to check all services
check_all_services() {
    print_status "Checking service health..."

    local all_healthy=true

    wait_for_service "Node 1" 11080 || all_healthy=false
    wait_for_service "Node 2" 11081 || all_healthy=false
    wait_for_service "Node 3" 11082 || all_healthy=false
    wait_for_service "Validator" 11083 || all_healthy=false

    if [ "$all_healthy" = true ]; then
        print_success "All services are healthy and running!"
    else
        print_warning "Some services may not be fully operational"
    fi

    return 0
}

# Function to display service information
show_service_info() {
    echo
    echo "════════════════════════════════════════════════════════════"
    echo "                 DeCoin Services Running                    "
    echo "════════════════════════════════════════════════════════════"
    echo
    echo "  🌐 Frontend:"
    echo "     • Web UI:     http://localhost:11000"
    echo
    echo "  📡 API Endpoints:"
    echo "     • Node 1:     http://localhost:11080"
    echo "     • Node 2:     http://localhost:11081"
    echo "     • Node 3:     http://localhost:11082"
    echo "     • Validator:  http://localhost:11083"
    echo
    echo "  📚 Documentation:"
    echo "     • Swagger UI: http://localhost:11080/docs"
    echo "     • Redoc:      http://localhost:11080/redoc"
    echo
    echo "  🔧 Useful Commands:"
    echo "     • View logs:       docker-compose logs -f"
    echo "     • Stop services:   docker-compose down"
    echo "     • View containers: docker-compose ps"
    echo "     • Run tests:       ./run_tests.sh"
    echo
    echo "════════════════════════════════════════════════════════════"
}

# Function to show container status
show_container_status() {
    echo
    print_status "Container Status:"
    docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null
}

# Function to optionally tail logs
tail_logs() {
    echo
    read -p "Would you like to tail the logs? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Tailing logs (press Ctrl+C to stop)..."
        docker-compose logs -f || docker compose logs -f
    fi
}

# Main execution
main() {
    echo "╔════════════════════════════════════════╗"
    echo "║     DeCoin Services Startup Script     ║"
    echo "╚════════════════════════════════════════╝"
    echo

    # Change to script directory
    cd "$(dirname "$0")"

    # Pre-flight checks
    print_status "Running pre-flight checks..."
    check_docker
    check_docker_compose
    check_ports

    # Build and start services
    build_images
    start_services

    # Wait for services to be healthy
    sleep 3  # Give containers time to initialize
    check_all_services

    # Show status and info
    show_container_status
    show_service_info

    # Optional log tailing
    tail_logs
}

# Handle script interruption
trap 'print_warning "Script interrupted by user"; exit 130' INT TERM

# Run main function
main "$@"