import pulumi
import pulumi_gcp as gcp

from components.config import DOMAIN, resource_name

# Bucket name must match the domain exactly — GCP requirement for
# custom domain hosting via backend bucket + load balancer.
_NAME_PREFIX = resource_name("frontend")


class FrontendOutputs:
    def __init__(
        self,
        bucket: gcp.storage.Bucket,
        ip_address: pulumi.Output[str],
        url: str,
    ) -> None:
        self.bucket = bucket
        self.ip_address = ip_address
        self.url = url


def create_frontend() -> FrontendOutputs:
    """
    Creates the static frontend hosting infrastructure for the stack domain.

    Architecture:
      browser → Global Load Balancer (SSL termination, static IP)
             → Backend Bucket
             → GCS Bucket (serves static files)

    The load balancer is necessary for two reasons:
      1. SSL termination — GCS cannot serve HTTPS on a custom domain alone.
         Google-managed certificates are provisioned automatically and
         auto-renewed at no cost.
      2. Custom domain routing — maps the domain to the GCS bucket.

    The bucket is publicly readable (allUsers → objectViewer) because every
    browser needs to fetch index.html, JS, CSS directly. Unlike the media
    bucket (private, signed URLs), there is no sensitive content here.

    HTTP (port 80) is redirected to HTTPS. No plaintext traffic reaches
    the bucket.

    SPA routing: both main_page_suffix and not_found_page are set to
    index.html. This means all paths (including deep links like
    /projects/123) return index.html and React Router handles routing
    client-side. Without not_found_page=index.html, deep links return 404.

    CDN is disabled for now — the load balancer is CDN-capable but we
    don't need the caching layer yet. Enable by setting enable_cdn=True
    on the BackendBucket resource.

    Deletion order:
      GCP enforces a strict outside-in deletion order for load balancer
      resources. Pulumi infers some of these from output references but
      not all — particularly the forwarding rules' dependency on proxies
      is through a string self_link that Pulumi may not trace deep enough.
      We declare the full chain explicitly with depends_on so that on
      destroy/replace Pulumi serialises deletions correctly:

        forwarding rules → proxies → url maps + ssl cert → backend bucket

      Without this, Pulumi attempts parallel deletion and GCP rejects it
      with "resource is already being used by another resource" errors.

    DNS records required (add at your registrar after pulumi up):
      A    <domain>  →  <frontend_ip output>
      (TXT record for domain verification if prompted by GCP)
    """

    # ── Bucket ────────────────────────────────────────────────────────────────

    bucket = gcp.storage.Bucket(
        "frontend-bucket",
        name=DOMAIN,
        location="US",
        uniform_bucket_level_access=True,
        # force_destroy allows Pulumi to delete this bucket even if it contains
        # objects. Safe for the frontend bucket — contents are build artifacts
        # that are always reproducible with make deploy-frontend. This prevents
        # "bucket not empty" errors on pulumi destroy or stack renames.
        # NOTE: do NOT set force_destroy on the media bucket — that holds user
        # data which cannot be regenerated.
        force_destroy=True,
        # SPA hosting config: serve index.html for / and all unknown paths.
        website=gcp.storage.BucketWebsiteArgs(
            main_page_suffix="index.html",
            not_found_page="index.html",
        ),
        # CORS: browsers need this to load assets from the same domain.
        cors=[
            gcp.storage.BucketCorArgs(
                origins=["*"],
                methods=["GET", "HEAD"],
                response_headers=["Content-Type"],
                max_age_seconds=3600,
            )
        ],
    )

    # Public read access — every browser fetches these files directly.
    gcp.storage.BucketIAMMember(
        "frontend-bucket-public-read",
        bucket=bucket.name,
        role="roles/storage.objectViewer",
        member="allUsers",
    )

    # ── Load Balancer ─────────────────────────────────────────────────────────

    # Static global IP — your DNS A record points at this forever.
    # Global (not regional) because the HTTPS load balancer is global.
    ip = gcp.compute.GlobalAddress(
        "frontend-ip",
        name=f"{_NAME_PREFIX}-ip",
        description="Static IP for the storyengine dev frontend load balancer",
    )

    # Backend bucket — the LB target that serves files from GCS.
    # enable_cdn=False for now. Flip to True when caching is needed.
    backend_bucket = gcp.compute.BackendBucket(
        "frontend-backend-bucket",
        name=f"{_NAME_PREFIX}-backend",
        bucket_name=bucket.name,
        enable_cdn=False,
        description="Serves static frontend assets from GCS",
    )

    # URL map — routes all requests to the backend bucket.
    # For a pure static site this is trivial: everything goes to the bucket.
    url_map = gcp.compute.URLMap(
        "frontend-url-map",
        name=f"{_NAME_PREFIX}-urlmap",
        default_service=backend_bucket.self_link,
        description="Routes all traffic to the frontend GCS bucket",
    )

    # Google-managed SSL certificate — GCP provisions and auto-renews.
    # Free. Provisioning takes 10-30 minutes after DNS propagates.
    # Status check: gcloud compute ssl-certificates describe <name> --global
    ssl_cert = gcp.compute.ManagedSslCertificate(
        "frontend-ssl-cert",
        name=f"{_NAME_PREFIX}-cert",
        managed=gcp.compute.ManagedSslCertificateManagedArgs(
            domains=[f"{DOMAIN}."],
        ),
        description=f"Google-managed SSL certificate for {DOMAIN}",
    )

    # HTTPS proxy — terminates SSL using the managed cert.
    # depends_on url_map and ssl_cert explicitly so Pulumi deletes this proxy
    # before either of them on destroy/replace (GCP rejects deleting a cert
    # or url map while a proxy still references it).
    https_proxy = gcp.compute.TargetHttpsProxy(
        "frontend-https-proxy",
        name=f"{_NAME_PREFIX}-https-proxy",
        url_map=url_map.self_link,
        ssl_certificates=[ssl_cert.self_link],
        opts=pulumi.ResourceOptions(depends_on=[url_map, ssl_cert]),
    )

    # Forwarding rule — binds the static IP + port 443 to the HTTPS proxy.
    # depends_on the proxy explicitly so Pulumi deletes this forwarding rule
    # before the proxy on destroy/replace (GCP rejects deleting a proxy while
    # a forwarding rule still references it).
    gcp.compute.GlobalForwardingRule(
        "frontend-https-forwarding-rule",
        name=f"{_NAME_PREFIX}-https-rule",
        ip_address=ip.address,
        ip_protocol="TCP",
        port_range="443",
        target=https_proxy.self_link,
        load_balancing_scheme="EXTERNAL",
        opts=pulumi.ResourceOptions(depends_on=[https_proxy]),
    )

    # ── HTTP → HTTPS redirect ─────────────────────────────────────────────────

    # All port 80 traffic is redirected to HTTPS.
    # Uses a separate URL map that returns a 301 redirect for every request.
    redirect_url_map = gcp.compute.URLMap(
        "frontend-redirect-url-map",
        name=f"{_NAME_PREFIX}-redirect-urlmap",
        default_url_redirect=gcp.compute.URLMapDefaultUrlRedirectArgs(
            https_redirect=True,
            strip_query=False,
        ),
    )

    # depends_on redirect_url_map explicitly so Pulumi deletes this proxy
    # before the url map on destroy/replace.
    http_proxy = gcp.compute.TargetHttpProxy(
        "frontend-http-proxy",
        name=f"{_NAME_PREFIX}-http-proxy",
        url_map=redirect_url_map.self_link,
        opts=pulumi.ResourceOptions(depends_on=[redirect_url_map]),
    )

    # depends_on the http proxy explicitly so Pulumi deletes this forwarding
    # rule before the proxy on destroy/replace.
    gcp.compute.GlobalForwardingRule(
        "frontend-http-forwarding-rule",
        name=f"{_NAME_PREFIX}-http-rule",
        ip_address=ip.address,
        ip_protocol="TCP",
        port_range="80",
        target=http_proxy.self_link,
        load_balancing_scheme="EXTERNAL",
        opts=pulumi.ResourceOptions(depends_on=[http_proxy]),
    )

    return FrontendOutputs(
        bucket=bucket,
        ip_address=ip.address,
        url=f"https://{DOMAIN}",
    )
