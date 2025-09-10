#!/bin/bash

echo "Running DeCoin Example"
echo "====================="

cd "$(dirname "$0")"

echo "Installing dependencies..."
pip install -r requirements.txt

echo -e "\nRunning example usage..."
python examples/example_usage.py

echo -e "\nTo start a node, run:"
echo "  python src/node.py --config config/node1.json"
echo ""
echo "To start a second node:"
echo "  python src/node.py --config config/node2.json"
echo ""
echo "API endpoints will be available at:"
echo "  Node 1: http://localhost:8080"
echo "  Node 2: http://localhost:8081"