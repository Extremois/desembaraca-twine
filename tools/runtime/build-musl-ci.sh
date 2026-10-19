#!/bin/sh
# Executed only inside a disposable pinned Alpine image on matching host CPU.
set -eu
umask 022
arch="$1"
work="$2"
case "$arch" in x86_64|aarch64) ;; *) exit 2 ;; esac
test "$(uname -m)" = "$arch"
mkdir -p "$work"
mkdir "$work/evidence"
retain() {
    for name in sdk/sdk-record.json build/provenance.json build/static-elf-inspection.txt linked/provenance.json linked/static-elf-inspection.txt package/candidate.json package/candidate.zip; do
        if test -f "$work/$name"; then
            cp "$work/$name" "$work/evidence/$(basename "$name")"
            chmod 644 "$work/evidence/$(basename "$name")"
        fi
    done
}
trap retain EXIT
apk add --no-cache python3 cmake make bison flex binutils strace
cat /etc/os-release > "$work/os-release.txt"
apk info -vv | LC_ALL=C sort > "$work/apk-packages.txt"
uname -a > "$work/kernel.txt"
strace --kill-on-exit -qq true
python /workspace/tools/runtime/prepare-linux-ci.py --work "$work/sdk" --arch "$arch" --libc musl --environment-kind container
if ! python /workspace/tools/runtime/build-common.py --artifact-id "linux-musl-$arch" --source-archive "$work/sdk/graphviz.tar.gz" --sdk-record "$work/sdk/sdk-record.json" --output "$work/build" --execute > "$work/build.log" 2>&1; then
    cat "$work/build.log"
    exit 1
fi
cp "$work/build/provenance.json" "$work/evidence/parent-provenance.json"
chmod 644 "$work/evidence/parent-provenance.json"
python /workspace/tools/runtime/relink-zig.py --source-output "$work/build" --output "$work/linked" --zig "$work/sdk/sdk/zig-$arch-linux-0.15.2/zig"
python /workspace/tools/runtime/audit-graphviz-sources.py --source-build "$work/build" --linked-build "$work/linked" --source-archive "$work/sdk/graphviz.tar.gz" --report "$work/evidence/graphviz-source-evidence.json"
cp "$work/linked/build/cmd/dot/CMakeFiles/dot.dir/why-extract.tsv" "$work/evidence/why-extract.tsv"
cp "$work/linked/build/cmd/dot/CMakeFiles/dot.dir/link.d" "$work/evidence/link.d"
chmod 644 "$work/evidence/why-extract.tsv" "$work/evidence/link.d"
readelf --file-header --program-headers --dynamic --version-info "$work/linked/candidate/bin/dot" > "$work/elf.txt"
python /workspace/tools/runtime/observe-linux-network.py --build-output "$work/linked" --environment-kind container --report "$work/network-312.json" --corpus-report "$work/corpus-312.json"
python /workspace/tools/runtime/verify-artifact.py --root "$work/linked/candidate" --provenance "$work/linked/provenance.json" --write-inventory "$work/evidence/inventory.json" --static-elf
python /workspace/tools/runtime/pack-candidate.py --root "$work/linked/candidate" --inventory "$work/evidence/inventory.json" --provenance "$work/linked/provenance.json" --output "$work/package"
