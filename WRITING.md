## Publishing articles

Add a Markdown file under content/writing/ with YAML front matter: title, description, date (YYYY-MM-DD), tags (list), and draft (boolean). Filenames become URL slugs. Use ## headings; the template supplies the article title. Set draft: false after reviewing the article. Draft and future-dated articles are excluded from the build, index, and sitemap.

The Docker build installs pinned Python Markdown and YAML libraries in a separate build stage and generates static pages. The runtime remains the existing unprivileged NGINX image. No database or browser JavaScript is required. Build from a clean checkout; generated writing pages are not committed. This preserves the current HTML site without a full framework migration.

The introductory article is proposed copy for review. The kubeadm and traffic articles are unpublished outlines. The full topic backlog remains in blog-ideas.txt.
