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

The Kubernetes files are staged for a separate henryfranco-dev namespace. Routing is intentionally pending the ALB arrangement decision. Do not apply them until the ECR repository, node IAM pull permission, and linux/amd64 image exist.

Once those prerequisites are ready:

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply --dry-run=server -f kubernetes/
kubectl apply -f kubernetes/
kubectl rollout status deployment/henryfranco-dev -n henryfranco-dev --timeout=120s
kubectl port-forward service/henryfranco-dev -n henryfranco-dev 8080:80
```

The app is stateless: two replicas with RollingUpdate, a soft preference for different nodes, health probes, and a PodDisruptionBudget. No PVC is needed. The NodePort Service supports ALB instance targets because the existing Calico pod addresses are not directly routed in the VPC. NetworkPolicy allows VPC source addresses, matching the existing cluster's ALB-to-node traffic path.

A separate namespace cannot be routed by simply adding a backend to the current Spotify Ingress. An explicit IngressGroup could share an ALB across namespaces, but changing the current implicit group creates a new ALB and requires a coordinated DNS cutover. Keep the existing site live until the new HTTPS endpoint is verified.

The NGINX base is pinned to the multi-platform digest tested by CI. Update it deliberately and rerun the container checks.

Build linux/amd64 for the current EC2 nodes. Use a unique image version and deploy the published ECR digest.
The AWS ECR credential provider on the nodes supplies pull credentials; this site needs no image-pull Secret.

The site’s content is in site/index.html and its styling is in site/styles.css. Add work history or certifications only when the facts have been confirmed.

## Search Console after publication

Add henryfranco.dev as a Domain property in Google Search Console and verify ownership with its DNS TXT record. Submit https://henryfranco.dev/sitemap.xml, inspect the homepage, and request indexing.

Link the personal website from your public profiles. Search ranking is not guaranteed, and sitemap submission does not guarantee indexing.
