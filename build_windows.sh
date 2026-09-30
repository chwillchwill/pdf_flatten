#!/usr/bin/env bash
# Build the Windows .exe from WSL using the Windows Python launcher (py.exe).
# The build runs in a copy under %TEMP% because cmd.exe cannot run from a \\wsl$ path.
#
#   ./build_windows.sh         build dist/PDFFlattener.exe
#   ./build_windows.sh clean   remove the %TEMP% build copy (including its venv),
#                              plus build output and caches in this project
set -euo pipefail
cd "$(dirname "$0")"

win_temp=$(cmd.exe /c "echo %TEMP%" 2>/dev/null | tr -d '\r')
[ -n "$win_temp" ] || { echo "Could not find the Windows %TEMP% folder." >&2; exit 1; }
build_dir=$(wslpath "$win_temp\\pdf_flattener_build")

if [ "${1:-}" = "clean" ]; then
    rm -rf -- "$build_dir" dist build __pycache__ tests/__pycache__ .pytest_cache ./*.spec
    echo "Cleaned."
    exit 0
fi

mkdir -p "$build_dir"
cp pdf_flattener.py requirements.txt requirements-build.txt build.bat "$build_dir/"
(cd "$build_dir" && cmd.exe /c build.bat)

mkdir -p dist
cp "$build_dir/dist/PDFFlattener.exe" dist/
# Keep only the venv in the temp copy so the next build is faster.
rm -rf -- "$build_dir/build" "$build_dir/dist" "$build_dir"/*.spec
echo "Copied to $(pwd)/dist/PDFFlattener.exe"
