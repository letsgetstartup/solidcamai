#!/bin/bash
# scripts/release/build_release.sh
set -e

VERSION=$(cat VERSION)
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "--- Building SIMCO AI Release v$VERSION ($GIT_SHA) ---"

mkdir -p dist

# 1. Build Python Wheel
python3 -m pip install --upgrade build
python3 -m build --wheel --sdist --outdir dist/

# 2. Build Docker Image (tagging only, no push)
# docker build -t simco-agent:$VERSION -t simco-agent:$VERSION-$GIT_SHA .

# 3. Generate Manifest
MANIFEST_PATH="dist/release_manifest.json"
cat > $MANIFEST_PATH <<EOF
{
  "version": "$VERSION",
  "git_sha": "$GIT_SHA",
  "build_time_utc": "$BUILD_TIME",
  "artifacts": [
    {
      "name": "$(basename dist/*.whl)",
      "sha256": "$( (sha256sum dist/*.whl 2>/dev/null || shasum -a 256 dist/*.whl) | cut -d' ' -f1 )"
    }
  ],
  "dependencies": $(python3 -c "import json; print(json.dumps(open('requirements.txt').read().splitlines()))")
}
EOF

echo "✅ Release build complete: $MANIFEST_PATH"
