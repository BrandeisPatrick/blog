#!/bin/sh
# Fetch the pinned rtk release binary into .cache/bin and verify its checksum.
set -eu
cd "$(dirname "$0")/.."
VER=v0.49.0
ASSET=rtk-aarch64-apple-darwin.tar.gz
SHA=bbbfebabb22686993a80da731aa4d5d35116fb8ae24abb00608efa028e13ae01
mkdir -p .cache/bin .cache/dl
curl -sfL -o ".cache/dl/$ASSET" "https://github.com/rtk-ai/rtk/releases/download/$VER/$ASSET"
GOT=$(shasum -a 256 ".cache/dl/$ASSET" | awk '{print $1}')
[ "$GOT" = "$SHA" ] || { echo "rtk checksum mismatch: $GOT" >&2; exit 1; }
tar -xzf ".cache/dl/$ASSET" -C .cache/bin
rm -rf .cache/dl
.cache/bin/rtk --version
