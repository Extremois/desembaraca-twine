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
    for name in sdk/sdk-record.json build/provenance.json build/static-elf-inspection.txt linked/provenance.json linked/static-elf-inspection.txt notices/provenance.json notices/static-elf-inspection.txt notices/review.json package/candidate.json package/candidate.zip; do
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
cp "$work/linked/provenance.json" "$work/evidence/linked-provenance.json"
chmod 644 "$work/evidence/linked-provenance.json"
python /workspace/tools/runtime/audit-musl-objects.py --linked-build "$work/linked" --sdk-root "$work/sdk/sdk/zig-$arch-linux-0.15.2" --sdk-archive "$work/sdk/zig.tar.xz" --report "$work/evidence/musl-object-evidence.json"
python /workspace/tools/runtime/audit-zig-runtime.py --linked-build "$work/linked" --sdk-root "$work/sdk/sdk/zig-$arch-linux-0.15.2" --sdk-archive "$work/sdk/zig.tar.xz" --report "$work/evidence/zig-runtime-evidence.json"
python /workspace/tools/runtime/audit-graphviz-data.py --source-build "$work/build" --linked-build "$work/linked" --source-archive "$work/sdk/graphviz.tar.gz" --compiler-evidence "$work/evidence/graphviz-source-evidence.json" --report "$work/evidence/graphviz-data-evidence.json"
python /workspace/tools/runtime/prepare-draft-notices.py --linked-build "$work/linked" --source-build "$work/build" --evidence "$work/evidence/graphviz-source-evidence.json" --graphviz-archive "$work/sdk/graphviz.tar.gz" --sdk-archive "$work/sdk/zig.tar.xz" --sdk-root "$work/sdk/sdk/zig-$arch-linux-0.15.2" --musl-object-evidence "$work/evidence/musl-object-evidence.json" --zig-runtime-evidence "$work/evidence/zig-runtime-evidence.json" --data-evidence "$work/evidence/graphviz-data-evidence.json" --output "$work/notices"
readelf --file-header --program-headers --dynamic --version-info "$work/notices/candidate/bin/dot" > "$work/elf.txt"
python /workspace/tools/runtime/observe-linux-network.py --build-output "$work/notices" --environment-kind container --report "$work/network-312.json" --corpus-report "$work/corpus-312.json"
python /workspace/tools/runtime/verify-artifact.py --root "$work/notices/candidate" --provenance "$work/notices/provenance.json" --write-inventory "$work/evidence/inventory.json" --static-elf
python /workspace/tools/runtime/pack-candidate.py --root "$work/notices/candidate" --inventory "$work/evidence/inventory.json" --provenance "$work/notices/provenance.json" --output "$work/package"
python /workspace/tools/runtime/observe-linux-network.py --build-output "$work/notices" --private-package "$work/package" --environment-kind container --report "$work/runtime-network-312.json" --corpus-report "$work/runtime-corpus-312.json"
