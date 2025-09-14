#!/bin/bash

echo "=== Node Heights ==="
for port in 11080 11081 11082 11083 11084 11085 11086 11087; do
  height=$(curl -s "http://localhost:$port/status" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('chain_height', 0))" 2>/dev/null || echo "0")
  echo "Port $port: height $height"
done