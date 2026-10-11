# henryfranco.dev

Henry Franco’s personal website: a responsive static page inspired by the current site's typography, navy text, blue accents, and generous spacing.

The page includes a short bio, projects, public profiles, a canonical URL, ProfilePage/Person structured data, a sitemap, and robots.txt. It uses no JavaScript, external fonts, cookies, analytics, or personal credentials.

## Preview the container

```bash
docker build -t henryfranco-dev:preview .
docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -p 127.0.0.1:8080:8080 henryfranco-dev:preview
```

Open http://localhost:8080. The site is served by unprivileged NGINX on port 8080.
Only /tmp needs to be writable. The website has no persistent data or Secrets.

## Validation

GitHub Actions builds the image, validates NGINX configuration, and starts the container with a read-only filesystem, dropped capabilities, and no privilege escalation.
It checks real HTTP responses, metadata, JSON-LD, linked assets, discovery files, health checks, and 404 behavior.

## Kubernetes publication

The publication plan uses the existing kubeadm cluster and ECR. The ALB arrangement and DNS/certificate configuration are being prepared separately; this branch does not deploy or change DNS.

The workloads use the existing spotify-now-playing namespace so both sites can share the current Ingress and ALB without replacing it. Each site has its own Deployment, Service, labels, and NetworkPolicy. Do not apply them until the ECR repository, node IAM pull permission, and linux/amd64 image exist.

Once those prerequisites are ready:

```bash
kubectl apply --dry-run=server -f kubernetes/
kubectl apply -f kubernetes/
kubectl rollout status deployment/henryfranco-dev -n spotify-now-playing --timeout=120s
kubectl port-forward service/henryfranco-dev -n spotify-now-playing 8080:80
```

The app is stateless: two replicas with RollingUpdate, a soft preference for different nodes, health probes, and a PodDisruptionBudget. No PVC is needed. The NodePort Service supports ALB instance targets because the existing Calico pod addresses are not directly routed in the VPC. NetworkPolicy allows VPC source addresses, matching the existing cluster's ALB-to-node traffic path.

Apply the companion Spotify Ingress PR only after this workload is ready and the Route 53 ACM certificate is issued. It adds henryfranco.dev to the existing Ingress and discovers ACM certificates by hostname. Verify HTTPS directly against the ALB before enabling the Terraform DNS cutover switch.

The NGINX base is pinned to the multi-platform digest tested by CI. Update it deliberately and rerun the container checks.

Build linux/amd64 for the current EC2 nodes. Use a unique image version and deploy the published ECR digest.
The AWS ECR credential provider on the nodes supplies pull credentials; this site needs no image-pull Secret.

The site’s content is in site/index.html and its styling is in site/styles.css. Add work history or certifications only when the facts have been confirmed.

## Search Console after publication

Add henryfranco.dev as a Domain property in Google Search Console and verify ownership with its DNS TXT record. Submit https://henryfranco.dev/sitemap.xml, inspect the homepage, and request indexing.

Link the personal website from your public profiles. Search ranking is not guaranteed, and sitemap submission does not guarantee indexing.

## Publication order

1. Apply the Terraform ECR and IAM change in environments/kubernetes (workspace kubernetes).
2. Build and publish the image:

```bash
REGISTRY=643593783040.dkr.ecr.us-east-1.amazonaws.com
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$REGISTRY"
docker buildx build --platform linux/amd64 --tag "$REGISTRY/henryfranco-dev:0.1.0" --push .
```

3. Apply the Terraform certificate configuration in environments/public_endpoint with personal_site_dns_enabled=false. Confirm the henryfranco.dev certificate is ISSUED.
4. Apply the manifests above, then apply the companion shared Ingress change from spotify-now-playing.
5. Test before changing public DNS:

```bash
ALB_HOST=$(kubectl get ingress spotify-now-playing -n spotify-now-playing -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -fsS --connect-to "henryfranco.dev:443:${ALB_HOST}:443" https://henryfranco.dev/
```

6. Save the old Route 53 A/AAAA records for rollback. Enable personal_site_dns_enabled in Terraform, review the plan, and apply. Confirm https://henryfranco.dev/ before retiring the old hosting.

A future image release must use a new immutable ECR tag. Update the Deployment image through a PR. No commands here run automatically when the PR is merged.
