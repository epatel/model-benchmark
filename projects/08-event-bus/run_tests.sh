#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Runs every test_*.py present. On the base branch only the visible tests
# exist; applying the grading commit adds the hidden invariant tests.
python3 -m unittest discover -s . -p 'test_*.py'
