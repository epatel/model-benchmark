#!/usr/bin/env bash
# Pack the answer key (SOLUTION.md + hidden tests from the grading branch) into
# an encrypted archive `grading.enc` that is safe to commit to the public repo.
# Crawlers/model-training see only ciphertext; anyone with the password can
# reconstruct the grading branch with scripts/unpack_grading.sh.
#
#   scripts/pack_grading.sh            # prompts for a password
#   GRADING_PASS=... scripts/pack_grading.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -n "${BENCH_BASE:-}" ]; then BASE="$BENCH_BASE"
elif git rev-parse --verify -q main >/dev/null; then BASE=main
else BASE=base; fi

git rev-parse --verify -q refs/heads/grading >/dev/null || { echo "no grading branch to pack"; exit 1; }

answers=()
while IFS= read -r f; do [ -n "$f" ] && answers+=("$f"); done \
  < <(git diff --name-only "$BASE" grading | grep -E 'SOLUTION|hidden')
[ ${#answers[@]} -gt 0 ] || { echo "no answer files found on grading"; exit 1; }

if [ -n "${GRADING_PASS:-}" ]; then PACKPW="$GRADING_PASS"
else read -rsp "grading password: " PACKPW; echo >&2; fi
[ -n "$PACKPW" ] || { echo "empty password"; exit 1; }
export PACKPW

git archive --format=tar grading -- "${answers[@]}" \
  | gzip \
  | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:PACKPW -out grading.enc
unset PACKPW

echo "wrote grading.enc (${#answers[@]} answer files, encrypted)."
echo "commit it:  git add grading.enc && git commit -m 'update encrypted grading bundle'"
echo "share the password out-of-band (never commit it)."
