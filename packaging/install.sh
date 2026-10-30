#!/usr/bin/env sh
set -eu

repo="Bibek200619/Omnix-CLI"
system=$(uname -s)
machine=$(uname -m)
case "$system:$machine" in
  Darwin:arm64|Darwin:aarch64) target=macos-aarch64 ;;
  Linux:x86_64|Linux:amd64) target=linux-x86_64 ;;
  *)
    printf 'Unsupported platform: %s/%s. Supported release builds: macOS arm64 and Linux x86_64.\n' "$system" "$machine" >&2
    exit 1
    ;;
esac

python=${OMNIX_INSTALL_PYTHON:-}
if [ -z "$python" ]; then
  for candidate in python3 python3.14 python3.13 python3.12; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' 2>/dev/null; then
      python=$candidate
      break
    fi
  done
fi
if [ -z "$python" ]; then
  printf 'Python 3.12 or newer is required. Install it, then run this installer again.\n' >&2
  exit 1
fi

data_home=${OMNIX_DATA_HOME:-${XDG_DATA_HOME:-"$HOME/.local/share"}}
bin_dir=${OMNIX_BIN_DIR:-"$HOME/.local/bin"}
install_dir="$data_home/omnix"
stage="$data_home/omnix-install-$$"
archive="omnix-$target.tar.gz"
release_base=${OMNIX_RELEASE_BASE_URL:-"https://github.com/$repo/releases/latest/download"}
asset="$release_base/$archive"
mkdir -p "$data_home" "$bin_dir" "$stage"
trap 'rm -rf "$stage"' EXIT

if command -v curl >/dev/null 2>&1; then
  curl --fail --location --silent --show-error "$asset" -o "$stage/$archive"
  curl --fail --location --silent --show-error \
    "$release_base/SHA256SUMS" -o "$stage/release-SHA256SUMS"
else
  printf 'curl is required to download the Omnix release.\n' >&2
  exit 1
fi
grep " $archive$" "$stage/release-SHA256SUMS" > "$stage/archive-checksum"
if command -v shasum >/dev/null 2>&1; then
  (cd "$stage" && shasum -a 256 -c archive-checksum)
elif command -v sha256sum >/dev/null 2>&1; then
  (cd "$stage" && sha256sum -c archive-checksum)
else
  printf 'A SHA-256 utility (shasum or sha256sum) is required.\n' >&2
  exit 1
fi
tar -xzf "$stage/$archive" -C "$stage"
if command -v shasum >/dev/null 2>&1; then
  (cd "$stage" && shasum -a 256 -c SHA256SUMS)
elif command -v sha256sum >/dev/null 2>&1; then
  (cd "$stage" && sha256sum -c SHA256SUMS)
else
  printf 'A SHA-256 utility (shasum or sha256sum) is required.\n' >&2
  exit 1
fi

"$python" -m venv "$stage/venv"
"$stage/venv/bin/python" -m pip install --require-hashes -r "$stage/requirements.txt"
"$stage/venv/bin/python" -m pip install --no-deps "$stage"/*.whl
mkdir -p "$stage/bin"
install -m 0755 "$stage/omnix" "$stage/bin/omnix"
printf '%s\n' "$bin_dir" > "$stage/.bin-dir"
rm -f "$stage/$archive" "$stage/release-SHA256SUMS" "$stage/archive-checksum" \
  "$stage/omnix" "$stage"/*.whl "$stage/requirements.txt" "$stage/SHA256SUMS"
rm -rf "$install_dir.previous"
if [ -e "$install_dir" ]; then mv "$install_dir" "$install_dir.previous"; fi
if mv "$stage" "$install_dir"; then
  rm -rf "$install_dir.previous"
else
  if [ -e "$install_dir.previous" ]; then mv "$install_dir.previous" "$install_dir"; fi
  exit 1
fi

cat > "$bin_dir/omnix" <<'LAUNCHER'
#!/usr/bin/env sh
set -eu
launcher_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OMNIX_HOME=${OMNIX_HOME:-$(cat "$launcher_dir/omnix.home")}
export OMNIX_PYTHON="$OMNIX_HOME/venv/bin/python"
exec "$OMNIX_HOME/bin/omnix" "$@"
LAUNCHER
printf '%s\n' "$install_dir" > "$bin_dir/omnix.home"
chmod 0755 "$bin_dir/omnix"
printf 'Omnix installed. Run %s/omnix.\n' "$bin_dir"
case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *) printf 'Add %s to PATH to run `omnix` from any terminal.\n' "$bin_dir" ;;
esac
