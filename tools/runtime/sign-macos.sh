#!/bin/sh
# Explicit maintainer action; credentials must already exist in the Keychain.
set -eu
script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
exec python3 "$script_dir/sign-macos.py" "$@"
