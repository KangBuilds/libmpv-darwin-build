"""Verify every dylib load command in an extracted XCFramework archive.

Xcode 27 SDKs carry a whole-dylib `$ld$previous$` entry in CoreMedia.tbd
that makes ld record CoreMedia as the Swift overlay
(`@rpath/SwiftCoreMedia.framework/SwiftCoreMedia` in 27.1,
`@rpath/libswiftCoreMedia.dylib` in 27.2) whenever the iOS deployment target
is below 12.2. Neither path exists in an app, so dyld aborts at launch.

Each slice must only load system libraries or frameworks shipped in the
same archive, never a Swift overlay, and must target iOS 12.2 or later.
"""

import pathlib
import re
import subprocess
import sys

MIN_IOS = (12, 2)
SYSTEM_PREFIXES = ("/System/Library/", "/usr/lib/")

root = pathlib.Path(sys.argv[1])
frameworks = sorted(root.glob("*/*.xcframework"))
assert frameworks, "No XCFrameworks found"
shipped = {framework.stem for framework in frameworks}

errors = []
checked = 0
for framework in frameworks:
    for binary in sorted(framework.glob("*/*.framework/*")):
        if binary.name != binary.parent.stem or not binary.is_file():
            continue
        archs = subprocess.run(
            ["lipo", "-archs", str(binary)],
            check=True, capture_output=True, text=True,
        ).stdout.split()
        assert archs, binary
        for arch in archs:
            checked += 1
            where = f"{binary.relative_to(root)} ({arch})"
            loads = subprocess.run(
                ["otool", "-arch", arch, "-L", str(binary)],
                check=True, capture_output=True, text=True,
            ).stdout.splitlines()[1:]
            own_id = f"@rpath/{binary.name}.framework/{binary.name}"
            for line in loads:
                path = line.strip().split(" (compatibility")[0]
                if "swift" in path.lower():
                    errors.append(f"{where}: Swift overlay load {path}")
                elif path == own_id or path.startswith(SYSTEM_PREFIXES):
                    continue
                elif m := re.fullmatch(r"@rpath/(\w+)\.framework/\1", path):
                    if m.group(1) not in shipped:
                        errors.append(f"{where}: unshipped framework {path}")
                else:
                    errors.append(f"{where}: unexpected load {path}")

            build = subprocess.run(
                ["vtool", "-arch", arch, "-show-build", str(binary)],
                check=True, capture_output=True, text=True,
            ).stdout
            m = re.search(r"minos (\d+)\.(\d+)", build)
            if not m:
                errors.append(f"{where}: no minos in LC_BUILD_VERSION")
            elif tuple(map(int, m.groups())) < MIN_IOS:
                errors.append(f"{where}: minos {m.group(1)}.{m.group(2)} < 12.2")

assert checked, "No framework binaries found"
if errors:
    print("\n".join(errors))
    sys.exit(f"{len(errors)} load command problem(s) in {checked} slices")
print(f"{checked} slices: load commands and minimum iOS versions verified")
