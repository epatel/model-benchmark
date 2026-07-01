#!/usr/bin/env bash
# Reconstruct the grading branch from the encrypted bundle (grading.enc), so a
# clone with only the public `main` branch can grade. Requires the password.
# Builds the branch with git plumbing — the working tree / current branch are
# never touched.
#
#   scripts/unpack_grading.sh          # prompts for a password; builds `grading`
#   GRADING_PASS=... scripts/unpack_grading.sh
#   GRADING_BRANCH=grading scripts/unpack_grading.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -n "${BENCH_BASE:-}" ]; then BASE="$BENCH_BASE"
elif git rev-parse --verify -q main >/dev/null; then BASE=main
else BASE=base; fi
BRANCH="${GRADING_BRANCH:-grading}"

[ -f grading.enc ] || { echo "grading.enc not found"; exit 1; }

if [ -n "${GRADING_PASS:-}" ]; then PACKPW="$GRADING_PASS"
else read -rsp "grading password: " PACKPW; echo >&2; fi
export PACKPW

TMP="$(mktemp -d)"
if ! openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:PACKPW -in grading.enc \
     | gunzip | tar -x -C "$TMP" 2>/dev/null; then
  unset PACKPW; rm -rf "$TMP"
  echo "decryption failed — wrong password or corrupt bundle"; exit 1
fi
unset PACKPW

# build BRANCH = BASE + one commit adding the extracted answer files (plumbing)
idx="$(mktemp -u)"; export GIT_INDEX_FILE="$idx"
git read-tree "$BASE"
n=0
while IFS= read -r rel; do
  blob="$(git hash-object -w "$TMP/$rel")"
  git update-index --add --cacheinfo "100644,$blob,$rel"
  n=$((n+1))
done < <(cd "$TMP" && find . -type f | sed 's|^\./||')
tree="$(git write-tree)"
commit="$(git commit-tree "$tree" -p "$(git rev-parse "$BASE")" -m "grading: hidden tests + SOLUTION.md (from bundle)")"
git update-ref "refs/heads/$BRANCH" "$commit"
unset GIT_INDEX_FILE; rm -f "$idx"; rm -rf "$TMP"

echo "reconstructed branch '$BRANCH' = $BASE + $n answer files ($(git rev-parse --short "$commit"))."
echo "you can now grade:  ./bench.sh start <model> && ./bench.sh grade <model>"
