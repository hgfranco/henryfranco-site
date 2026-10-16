# Image release scripts

Run ./scripts/build-image.sh followed by ./scripts/deploy-image.sh from your checkout.

The build script requires a clean working tree, switches to main, pulls with fast-forward only, logs in to ECR, and builds/pushes linux/amd64. Tags use the commit SHA. Existing tags reuse the published digest; other ECR errors stop the script.

A successful build atomically saves the full image digest in ignored .release/image.txt. A failed build leaves any previous saved release untouched; deploy only after a successful build. No credentials are saved there.

The deploy script uses k and the current Kubernetes context. Shell aliases are not inherited by scripts, so it defines k using kubectl when no executable k exists. It prints the context, updates the website container, and waits 180 seconds. Failures exit nonzero without automatic rollback.

You can also pass a full ECR image@sha256:digest as the deploy script's first argument, including from another machine.

AWS credentials, Docker/buildx, and cluster access must be configured. These scripts do not run automatically or update kubernetes/deployment.yaml; record the released digest there through a PR to keep configuration aligned.
