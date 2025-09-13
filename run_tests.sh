#!/bin/bash

# DeCoin Test Runner Script
# Runs unit and integration tests with coverage reporting

set -e

echo "========================================="
echo "DeCoin Test Suite"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt

# Run tests based on argument
case "$1" in
    unit)
        echo -e "\n${GREEN}Running Unit Tests...${NC}"
        pytest tests/unit/ -v --cov=src --cov-report=term-missing
        ;;
    
    integration)
        echo -e "\n${GREEN}Running Integration Tests...${NC}"
        pytest tests/integration/ -v --cov=src --cov-report=term-missing
        ;;
    
    coverage)
        echo -e "\n${GREEN}Running All Tests with Coverage Report...${NC}"
        pytest tests/ -v --cov=src --cov-report=html --cov-report=term
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    
    quick)
        echo -e "\n${GREEN}Running Quick Tests (no coverage)...${NC}"
        pytest tests/ -x --tb=short
        ;;
    
    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}Please specify a test file or pattern${NC}"
            echo "Example: $0 specific tests/unit/test_blockchain.py"
            exit 1
        fi
        echo -e "\n${GREEN}Running Specific Tests: $2${NC}"
        pytest "$2" -v
        ;;
    
    docker)
        echo -e "\n${GREEN}Running Tests in Docker...${NC}"
        docker build -t decoin-test -f Dockerfile.test .
        docker run --rm decoin-test
        ;;
    
    watch)
        echo -e "\n${GREEN}Running Tests in Watch Mode...${NC}"
        pytest-watch tests/ --clear
        ;;
    
    *)
        echo -e "\n${GREEN}Running All Tests...${NC}"
        pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml
        
        # Check if all tests passed
        if [ $? -eq 0 ]; then
            echo -e "\n${GREEN}✓ All tests passed!${NC}"
        else
            echo -e "\n${RED}✗ Some tests failed${NC}"
            exit 1
        fi
        ;;
esac

echo -e "\n========================================="
echo "Test run completed"
echo "========================================="