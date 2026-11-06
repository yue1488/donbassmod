#!/bin/sh
# Stand-alone checks of the pure-Java parts of the mod (no Minecraft, no Gradle needed; any JDK 17+).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
javac -d "$OUT" "$HERE/../src/main/java/com/donbass/mod/boss/BossMultiplier.java" "$HERE/selfcheck/BossMultiplierCheck.java"
java -cp "$OUT" BossMultiplierCheck
