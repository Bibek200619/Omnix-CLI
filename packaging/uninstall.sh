#!/usr/bin/env sh
set -eu
install_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
bin_dir=${OMNIX_BIN_DIR:-"$HOME/.local/bin"}
if [ -f "$install_dir/.bin-dir" ]; then
  bin_dir=$(cat "$install_dir/.bin-dir")
fi
rm -f "$bin_dir/omnix"
rm -f "$bin_dir/omnix.home"
rm -rf "$install_dir"
printf 'Removed the Omnix CLI runtime. Project folders and their .project data were not changed.\n'
