#!/bin/bash

echo "Running DeCoin Example"
echo "====================="

cd "$(dirname "$0")"

# Activate virtual environment or create if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo -e "\nRunning example usage..."
python examples/example_usage.py

echo -e "\nTo start a node, run:"
echo "  source venv/bin/activate && python src/node.py --config config/node1.json"
echo ""
echo "To start a second node:"
echo "  source venv/bin/activate && python src/node.py --config config/node2.json"
echo ""
echo "API endpoints will be available at:"
echo "  Node 1: http://localhost:8080"
echo "  Node 2: http://localhost:8081"