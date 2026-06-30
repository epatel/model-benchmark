#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Runs all *_test.go present. On the base branch only the visible test exists;
# applying the grading commit adds the hidden ones.
go test -race -count=20 ./...
