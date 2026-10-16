#!/usr/bin/env bash
set -euo pipefail

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
[[ $# -le 1 ]] || die "Usage: $0 [ECR_IMAGE@sha256:DIGEST]"
# Interactive aliases are not inherited by scripts; supply the k shortcut.
if ! command -v k >/dev/null 2>&1; then
  command -v kubectl >/dev/null 2>&1 || die "Install k or kubectl."
  k() { command kubectl "$@"; }
fi
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
RELEASE_FILE="$SCRIPT_DIR/../.release/image.txt"
if [[ $# -eq 1 ]]; then
  REFERENCE="$1"
else
  [[ -f "$RELEASE_FILE" ]] || die "No saved image. Run scripts/build-image.sh or pass an image digest."
  REFERENCE="$(cat "$RELEASE_FILE")"
fi
[[ "$REFERENCE" =~ ^643593783040\.dkr\.ecr\.us-east-1\.amazonaws\.com/henryfranco-dev@sha256:[a-f0-9]{64}$ ]] ||
  die "Expected the henryfranco-dev ECR image with a sha256 digest."
CONTEXT="$(k config current-context)"
printf 'Context: %s\nDeployment: spotify-now-playing/henryfranco-dev\nImage: %s\n' "$CONTEXT" "$REFERENCE"
k set image deployment/henryfranco-dev -n spotify-now-playing "website=$REFERENCE"
k rollout status deployment/henryfranco-dev -n spotify-now-playing --timeout=180s
printf 'Deployment completed.\n'
