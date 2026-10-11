# Move the personal site to henryfranco

The namespace and shared ALB routing are owned by k8s-infra. Apply its namespace
manifest first, then these application manifests. Both personal-site domains use
this one Deployment and Service. Spotify stays in spotify-now-playing.

The image is pinned to 0.5.0, the release containing the reviewed resume changes.
Verify that this linux/amd64 image was published to ECR before applying.
Future releases must update the checked-in image through a PR.

```bash
aws ecr describe-images --region us-east-1 --repository-name henryfranco-dev --image-ids imageTag=0.5.0
kubectl apply --dry-run=server -f kubernetes/
kubectl diff -f kubernetes/
kubectl apply -f kubernetes/
kubectl rollout status deployment/henryfranco-dev -n henryfranco --timeout=180s
kubectl get pods -n henryfranco -l app=henryfranco-dev -o wide
kubectl get endpointslices -n henryfranco -l kubernetes.io/service-name=henryfranco-dev
```

Review the diff; exit code 1 means differences exist. Applying namespaced manifests
creates a second workload and does not move or delete the old resources.

Keep externalTrafficPolicy: Local: ALB instance targets must reach a local ready
Pod, preserving the VPC source addresses allowed by the NetworkPolicy. The new
Service receives its own NodePort; do not copy the old Service's assigned port.

Follow k8s-infra's namespace migration guide to create and test the new ALB,
switch DNS with Terraform, and eventually remove the old website workload.
Do not delete the old workload until all domains work through the new ALB and
the rollback window has ended. There is no website PVC to move.

The namespace's default-deny policy blocks ingress and egress unless allowed.
The application policy allows inbound TCP/8080 from the VPC for ALB traffic.
This static NGINX site needs no outbound connections. Its links and assets on
other domains are requested by the visitor's browser, not by NGINX.

## Publish the updated stylesheet

This release versions the stylesheet URL and asks caches to revalidate responses,
so the resume border and compact layout load instead of an older CSS file.
Preview it locally before building/pushing the 0.5.0 image:

```bash
python3 -m http.server 8000 --directory site
```

Open http://localhost:8000/resume/. Then build from the merged main branch:

```bash
REGISTRY=643593783040.dkr.ecr.us-east-1.amazonaws.com
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$REGISTRY"
docker buildx build --platform linux/amd64 --tag "$REGISTRY/henryfranco-dev:0.5.0" --push .
```

If fixing the live stylesheet before namespace migration, update only the existing
website's image with kubectl set image deployment/henryfranco-dev -n
spotify-now-playing website=643593783040.dkr.ecr.us-east-1.amazonaws.com/henryfranco-dev:0.5.0,
then wait for its rollout. Do not apply the new namespace manifests until the
namespace has been created. Verify the new stylesheet URL and resume layout on
both public domains. This optional image-only rollout does not change routing.
