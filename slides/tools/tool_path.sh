#!/usr/bin/env bash
set -eu
case "$1" in
  chromium) names="chromium chromium-browser google-chrome"; app="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; package=chromium; binary=chromium ;;
  soffice) names="soffice libreoffice"; app="/Applications/LibreOffice.app/Contents/MacOS/soffice"; package=libreoffice; binary=soffice ;;
  *) echo "unknown tool $1" >&2; exit 2 ;;
esac
for name in $names; do
  if command -v "$name" >/dev/null; then command -v "$name"; exit 0; fi
done
if [ -x "$app" ]; then echo "$app"; exit 0; fi
if command -v nix >/dev/null; then
  echo "$(nix --extra-experimental-features 'nix-command flakes' build "nixpkgs#$package" --no-link --print-out-paths)/bin/$binary"
  exit 0
fi
echo "$1 is not installed" >&2
exit 1
