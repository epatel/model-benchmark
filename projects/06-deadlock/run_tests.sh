#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Runs all *_test.go present. On the base branch only the visible test exists;
# applying the grading commit adds the hidden ones. The tests carry their own
# 5s watchdog, so a deadlock fails fast instead of hanging.
go test -race -count=5 ./...
