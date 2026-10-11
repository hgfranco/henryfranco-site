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


Publish resume-fix release 0.5.0 from the merged main branch before applying this deployment. This PR does not modify website content or cache settings.
