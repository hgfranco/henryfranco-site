FROM python:3.13-alpine AS writing
WORKDIR /build
COPY requirements-build.txt ./
RUN pip install --no-cache-dir -r requirements-build.txt
COPY scripts/ scripts/
COPY content/ content/
COPY site/ site/
RUN python scripts/build_writing.py

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:15c994d10d6d78658721c3bcafff14cb281fba2a4bdf9d5ba92c416a472516e3
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=writing /build/site/ /usr/share/nginx/html/
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
