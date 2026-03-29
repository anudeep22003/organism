import pulumi
import pulumi_gcp as gcp

from components.config import API_DOMAIN, DOMAIN, REGION, resource_name

# Bucket name must match the domain exactly — GCP requirement for
# custom domain hosting via backend bucket + load balancer.
_NAME_PREFIX = resource_name("frontend")


class FrontendOutputs:
    def __init__(
        self,
        bucket: gcp.storage.Bucket,
        ip_address: pulumi.Output[str],
        url: str,
        api_url: str,
    ) -> None:
        self.bucket = bucket
        self.ip_address = ip_address
        self.url = url
        self.api_url = api_url


def create_frontend(service: gcp.cloudrunv2.Service) -> FrontendOutputs:
    """
    Creates the static frontend hosting infrastructure and API routing.

    Architecture:
      browser → single Global Load Balancer (one IP, one SSL cert)
             ├─ host: DOMAIN     → Backend Bucket → GCS (static frontend)
             └─ host: API_DOMAIN → Backend Service → Serverless NEG → Cloud Run

    Both domains share one Global IP, one SSL cert, one set of forwarding
    rules. This saves ~$36/month vs a dedicated API load balancer (which
    requires two additional forwarding rules billed at ~$18/month each).

    NOTE — decoupling the API LB:
      If a separate API load balancer is needed (e.g. for independent
      scaling, CDN config, or IAM restrictions on the Cloud Run URL),
      extract the following into components/backend_lb.py:
        - RegionNetworkEndpointGroup (neg)
        - BackendService (backend_service)
        - A new GlobalAddress, ManagedSslCertificate for API_DOMAIN only
        - A new URLMap, TargetHttpsProxy, GlobalForwardingRule (443 + 80)
      Then remove the api host_rule and path_matcher from this URL map,
      remove API_DOMAIN from the SSL cert domains, and add a new DNS
      A record for API_DOMAIN pointing at the new IP.

    Deletion order:
      GCP enforces strict outside-in deletion for load balancer resources.
      The full correct order is:

        forwarding rules (443 + 80)
          → proxies (https + http)
            → url maps + ssl cert
              → backend bucket + backend service
                → NEG + GCS bucket

      All depends_on chains are declared explicitly — Pulumi cannot always
      infer deletion order from self_link string references alone.

    DNS records required (add at registrar after pulumi up):
      A    DOMAIN      →  <frontend_ip output>
      A    API_DOMAIN  →  <frontend_ip output>  (same IP — shared LB)

    SSL cert provisioning:
      Google-managed certs provision asynchronously after DNS propagates.
      Adding API_DOMAIN to the cert triggers a replace (GCP does not allow
      in-place domain changes) — expect a brief HTTPS disruption (~minutes)
      while the new cert provisions. Status:
        gcloud compute ssl-certificates describe <name> --global
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

    # Static global IP — both DNS A records (DOMAIN + API_DOMAIN) point here.
    # Global (not regional) because the HTTPS load balancer is global.
    ip = gcp.compute.GlobalAddress(
        "frontend-ip",
        name=f"{_NAME_PREFIX}-ip",
        description="Static IP for the storyengine frontend + API load balancer",
    )

    # Backend bucket — the LB target that serves static files from GCS.
    backend_bucket = gcp.compute.BackendBucket(
        "frontend-backend-bucket",
        name=f"{_NAME_PREFIX}-backend",
        bucket_name=bucket.name,
        enable_cdn=False,
        description="Serves static frontend assets from GCS",
    )

    # ── API routing (Serverless NEG + Backend Service) ─────────────────────────

    # Serverless NEG — the bridge between the load balancer world (IPs/ports)
    # and Cloud Run (no fixed IPs). Points at the Cloud Run service by name.
    # Must be in the same region as the Cloud Run service.
    neg = gcp.compute.RegionNetworkEndpointGroup(
        "api-neg",
        name=f"{_NAME_PREFIX}-api-neg",
        network_endpoint_type="SERVERLESS",
        region=REGION,
        cloud_run=gcp.compute.RegionNetworkEndpointGroupCloudRunArgs(
            service=service.name,
        ),
    )

    # Backend Service — wraps the NEG and is referenced by the URL map.
    # protocol=HTTPS because Cloud Run only accepts HTTPS.
    # Must be deleted before the URL map on destroy (URL map references it).
    backend_service = gcp.compute.BackendService(
        "api-backend-service",
        name=f"{_NAME_PREFIX}-api-backend",
        protocol="HTTPS",
        load_balancing_scheme="EXTERNAL",
        backends=[
            gcp.compute.BackendServiceBackendArgs(
                group=neg.id,
            )
        ],
        opts=pulumi.ResourceOptions(depends_on=[neg]),
    )

    # ── URL Map (host-based routing) ──────────────────────────────────────────

    # Routes requests to the correct backend based on the Host: header.
    # DOMAIN → GCS bucket (static frontend assets)
    # API_DOMAIN → Cloud Run service (via Backend Service + NEG)
    # Default fallback → GCS bucket (handles bare IP requests, healthchecks)
    #
    # depends_on both backend targets so Pulumi deletes those resources
    # AFTER the URL map on destroy — GCP rejects deleting a backend while
    # any URL map still references it.
    url_map = gcp.compute.URLMap(
        "frontend-url-map",
        name=f"{_NAME_PREFIX}-urlmap",
        default_service=backend_bucket.self_link,
        host_rules=[
            gcp.compute.URLMapHostRuleArgs(
                hosts=[DOMAIN],
                path_matcher="frontend",
            ),
            gcp.compute.URLMapHostRuleArgs(
                hosts=[API_DOMAIN],
                path_matcher="api",
            ),
        ],
        path_matchers=[
            gcp.compute.URLMapPathMatcherArgs(
                name="frontend",
                default_service=backend_bucket.self_link,
            ),
            gcp.compute.URLMapPathMatcherArgs(
                name="api",
                default_service=backend_service.self_link,
            ),
        ],
        opts=pulumi.ResourceOptions(depends_on=[backend_bucket, backend_service]),
    )

    # Google-managed SSL certificate covering both domains.
    # GCP provisions and auto-renews. Free.
    # Trailing dot = fully-qualified domain name (GCP requirement).
    # Provisioning takes 10-30 minutes after DNS propagates for both domains.
    # Adding or removing a domain triggers a cert replace (not in-place update).
    ssl_cert = gcp.compute.ManagedSslCertificate(
        "frontend-ssl-cert",
        name=f"{_NAME_PREFIX}-cert-v2",  # GCP resource name kept as-is to avoid replace
        managed=gcp.compute.ManagedSslCertificateManagedArgs(
            domains=[f"{DOMAIN}.", f"{API_DOMAIN}."],
        ),
        description=f"Google-managed SSL certificate for {DOMAIN} and {API_DOMAIN}",
        opts=pulumi.ResourceOptions(
            # Create the new cert before deleting the old one on future domain
            # changes — GCP rejects deleting a cert while a proxy references it.
            # aliases reconciles the Pulumi logical name (frontend-ssl-cert-v2 →
            # frontend-ssl-cert) as a state-only rename with no GCP operation.
            delete_before_replace=False,
            aliases=[pulumi.Alias(name="frontend-ssl-cert-v2")],
        ),
    )

    # HTTPS proxy — terminates SSL using the managed cert.
    # depends_on url_map and ssl_cert explicitly so Pulumi deletes this proxy
    # before either of them on destroy/replace.
    https_proxy = gcp.compute.TargetHttpsProxy(
        "frontend-https-proxy",
        name=f"{_NAME_PREFIX}-https-proxy",
        url_map=url_map.self_link,
        ssl_certificates=[ssl_cert.self_link],
        opts=pulumi.ResourceOptions(depends_on=[url_map, ssl_cert]),
    )

    # Forwarding rule — binds the static IP + port 443 to the HTTPS proxy.
    # depends_on the proxy explicitly so Pulumi deletes this rule before the
    # proxy on destroy/replace.
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

    # All port 80 traffic (both domains) is redirected to HTTPS.
    redirect_url_map = gcp.compute.URLMap(
        "frontend-redirect-url-map",
        name=f"{_NAME_PREFIX}-redirect-urlmap",
        default_url_redirect=gcp.compute.URLMapDefaultUrlRedirectArgs(
            https_redirect=True,
            strip_query=False,
        ),
    )

    http_proxy = gcp.compute.TargetHttpProxy(
        "frontend-http-proxy",
        name=f"{_NAME_PREFIX}-http-proxy",
        url_map=redirect_url_map.self_link,
        opts=pulumi.ResourceOptions(depends_on=[redirect_url_map]),
    )

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
        api_url=f"https://{API_DOMAIN}",
    )
