#!/usr/bin/env bash
set -eu
deck="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
output="${2:-${deck%.pptx}_render}"
here="$(cd "$(dirname "$0")" && pwd)"
soffice="$(bash "$here/tool_path.sh" soffice)"
profile="$(mktemp -d)"
trap 'rm -rf "$profile"' EXIT
mkdir -p "$output"
if [ "$(uname)" = Linux ]; then
  sed "s|</fontconfig>|<dir>$here/fonts</dir></fontconfig>|" "$here/fonts.conf" >"$profile/fonts.conf"
  export FONTCONFIG_FILE="$profile/fonts.conf"
fi
pdf="$output/$(basename "${deck%.pptx}").pdf"
rm -f "$pdf"
"$soffice" -env:UserInstallation="file://$profile" --headless --convert-to pdf --outdir "$output" "$deck" >/dev/null || true
test -s "$pdf"
rm -f "$output"/slide-*.jpg
pdftoppm -jpeg -r 80 "$pdf" "$output/slide"
ls "$output"/slide-*.jpg | wc -l
