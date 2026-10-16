#!/usr/bin/env bash
set -euo pipefail

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
for tool in git aws docker; do
  command -v "$tool" >/dev/null 2>&1 || die "Required command missing: $tool"
done
SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR/.."
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
REGISTRY=643593783040.dkr.ecr.us-east-1.amazonaws.com
REGION=us-east-1
REPOSITORY=henryfranco-dev
IMAGE="$REGISTRY/$REPOSITORY"

[[ -z "$(git status --porcelain)" ]] || die "Commit or stash working tree changes before building."
git switch main
git pull --ff-only
TAG="site-$(git rev-parse --short=12 HEAD)"
docker buildx version >/dev/null
aws ecr get-login-password --region "$REGION" |
  docker login --username AWS --password-stdin "$REGISTRY"

# Reuse this commit's release instead of overwriting an immutable tag.
DIGEST="$(aws ecr describe-images --region "$REGION" \
  --repository-name "$REPOSITORY" --image-ids "imageTag=$TAG" \
  --query 'imageDetails[0].imageDigest' --output text 2>&1)" || {
  if [[ "$DIGEST" == *ImageNotFoundException* ]]; then
    docker buildx build --platform linux/amd64 --tag "$IMAGE:$TAG" --push .
    DIGEST="$(aws ecr describe-images --region "$REGION" \
      --repository-name "$REPOSITORY" --image-ids "imageTag=$TAG" \
      --query 'imageDetails[0].imageDigest' --output text)"
  else
    die "$DIGEST"
  fi
}
[[ "$DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]] || die "Invalid ECR digest: $DIGEST"
mkdir -p "$ROOT/.release"
TEMP_FILE="$(mktemp "$ROOT/.release/image.XXXXXX")"
trap 'rm -f -- "$TEMP_FILE"' EXIT
printf '%s@%s\n' "$IMAGE" "$DIGEST" > "$TEMP_FILE"
mv -- "$TEMP_FILE" "$ROOT/.release/image.txt"
trap - EXIT
printf 'Published: %s:%s\nDeploy reference: %s@%s\nSaved: %s/.release/image.txt\n' \
  "$IMAGE" "$TAG" "$IMAGE" "$DIGEST" "$ROOT"
