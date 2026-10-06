#!/bin/bash
# validate.sh — MVS self-validation
set -e
PASS=0; FAIL=0
SKILL_DIR="$(dirname "$(dirname "$0")")"
check() {
  [ "$2" = "true" ] && { echo "  PASS: $1"; PASS=$((PASS+1)); } || { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }
}
SKILL_NAME=$(basename "$SKILL_DIR")
echo "Validating: $SKILL_NAME"
[ -f "$SKILL_DIR/SKILL.md" ] && check "SKILL.md exists" "true" || check "SKILL.md exists" "false"
grep -q "## Examples" "$SKILL_DIR/SKILL.md" 2>/dev/null && check "Has Examples section" "true" || check "Has Examples section" "false"
grep -q "## Troubleshooting" "$SKILL_DIR/SKILL.md" 2>/dev/null && check "Has Troubleshooting section" "true" || check "Has Troubleshooting section" "false"
grep -q "## See Also" "$SKILL_DIR/SKILL.md" 2>/dev/null && check "Has See Also section" "true" || check "Has See Also section" "false"
refs_count=$(ls "$SKILL_DIR/references/" 2>/dev/null | wc -l)
[ "$refs_count" -gt 0 ] && check "references/ non-empty" "true" || check "references/ non-empty" "false"
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
