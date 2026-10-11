#!/bin/sh
set -eu
rust_archive=/tmp/search-swe-rust.tar.xz
curl --fail --location --retry 3 \
  https://static.rust-lang.org/dist/2025-03-18/rust-1.85.1-x86_64-unknown-linux-gnu.tar.xz \
  --output "$rust_archive"
printf '%s  %s\n' 912c76f602f5f630138fca2388b2688c2c1aabcf823d71890b2b9155f743792e "$rust_archive" | sha256sum --check -
tar -xJf "$rust_archive" -C /tmp
/tmp/rust-1.85.1-x86_64-unknown-linux-gnu/install.sh \
  --prefix=/opt/rust --disable-ldconfig \
  --components=rustc,rust-std-x86_64-unknown-linux-gnu,cargo
rm -rf "$rust_archive" /tmp/rust-1.85.1-x86_64-unknown-linux-gnu
/opt/rust/bin/rustc --version | grep -F 'rustc 1.85.1 '
