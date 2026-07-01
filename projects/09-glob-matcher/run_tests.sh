#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Runs every test_*.py present (grading adds the hidden ones).
python3 -m unittest discover -s . -p 'test_*.py'
