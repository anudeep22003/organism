"""
Frontend hosting and API routing component.

Creates the complete frontend infrastructure: GCS bucket for static assets,
a Global HTTPS Load Balancer that routes both the frontend domain (GCS) and
the API domain (Cloud Run via Serverless NEG) using host-based routing.

Usage:
    frontend = Frontend("frontend", service=service.service)
    frontend.bucket      # gcp.storage.Bucket
    frontend.ip_address  # pulumi.Output[str] — the static global IP
    frontend.url         # str — https://<DOMAIN>
    frontend.api_url     # str — https://<API_DOMAIN>

Attributes exposed:
    bucket     (gcp.storage.Bucket): the GCS bucket serving static assets
    ip_address (pulumi.Output[str]): the static global IP address value
    url        (str): the frontend URL (https://<DOMAIN>)
    api_url    (str): the API URL (https://<API_DOMAIN>)

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

import pulumi
import pulumi_gcp as gcp

from components.config import APP, API_DOMAIN, DOMAIN, REGION, resource_name


class Frontend(pulumi.ComponentResource):
    """
    Static frontend hosting and API routing via a shared Global Load Balancer.

    Creates the GCS bucket for static assets, the complete HTTPS load balancer
    with host-based routing (frontend vs API), and the HTTP→HTTPS redirect.

    Child resources (all parented to this component):
        {name}-bucket                   gcp.storage.Bucket
        {name}-bucket-public-read       gcp.storage.BucketIAMMember
        {name}-ip                       gcp.compute.GlobalAddress
        {name}-backend-bucket           gcp.compute.BackendBucket
        {name}-api-neg                  gcp.compute.RegionNetworkEndpointGroup
        {name}-api-backend-service      gcp.compute.BackendService
        {name}-url-map                  gcp.compute.URLMap
        {name}-ssl-cert                 gcp.compute.ManagedSslCertificate
        {name}-https-proxy              gcp.compute.TargetHttpsProxy
        {name}-https-rule               gcp.compute.GlobalForwardingRule
        {name}-redirect-url-map         gcp.compute.URLMap
        {name}-http-proxy               gcp.compute.TargetHttpProxy
        {name}-http-rule                gcp.compute.GlobalForwardingRule
    """

    bucket: gcp.storage.Bucket
    ip_address: pulumi.Output[str]
    url: str
    api_url: str

    def __init__(
        self,
        name: str,
        service: gcp.cloudrunv2.Service,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:Frontend", name, {}, opts)

        name_prefix = resource_name("frontend")

        # ── Bucket ────────────────────────────────────────────────────────────

        self.bucket = gcp.storage.Bucket(
            f"{name}-bucket",
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
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Public read access — every browser fetches these files directly.
        gcp.storage.BucketIAMMember(
            f"{name}-bucket-public-read",
            bucket=self.bucket.name,
            role="roles/storage.objectViewer",
            member="allUsers",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ── Load Balancer ─────────────────────────────────────────────────────

        # Static global IP — both DNS A records (DOMAIN + API_DOMAIN) point here.
        # Global (not regional) because the HTTPS load balancer is global.
        ip = gcp.compute.GlobalAddress(
            f"{name}-ip",
            name=f"{name_prefix}-ip",
            description="Static IP for the storyengine frontend + API load balancer",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.ip_address = ip.address

        # Backend bucket — the LB target that serves static files from GCS.
        backend_bucket = gcp.compute.BackendBucket(
            f"{name}-backend-bucket",
            name=f"{name_prefix}-backend",
            bucket_name=self.bucket.name,
            enable_cdn=False,
            description="Serves static frontend assets from GCS",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ── API routing (Serverless NEG + Backend Service) ─────────────────────

        # Serverless NEG — the bridge between the load balancer world (IPs/ports)
        # and Cloud Run (no fixed IPs). Points at the Cloud Run service by name.
        # Must be in the same region as the Cloud Run service.
        neg = gcp.compute.RegionNetworkEndpointGroup(
            f"{name}-api-neg",
            name=f"{name_prefix}-api-neg",
            network_endpoint_type="SERVERLESS",
            region=REGION,
            cloud_run=gcp.compute.RegionNetworkEndpointGroupCloudRunArgs(
                service=service.name,
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Backend Service — wraps the NEG and is referenced by the URL map.
        # protocol=HTTPS because Cloud Run only accepts HTTPS.
        # Must be deleted before the URL map on destroy (URL map references it).
        backend_service = gcp.compute.BackendService(
            f"{name}-api-backend-service",
            name=f"{name_prefix}-api-backend",
            protocol="HTTPS",
            load_balancing_scheme="EXTERNAL",
            backends=[
                gcp.compute.BackendServiceBackendArgs(
                    group=neg.id,
                )
            ],
            opts=pulumi.ResourceOptions(parent=self, depends_on=[neg]),
        )

        # ── URL Map (host-based routing) ──────────────────────────────────────

        # Routes requests to the correct backend based on the Host: header.
        # DOMAIN → GCS bucket (static frontend assets)
        # API_DOMAIN → Cloud Run service (via Backend Service + NEG)
        # Default fallback → GCS bucket (handles bare IP requests, healthchecks)
        #
        # depends_on both backend targets so Pulumi deletes those resources
        # AFTER the URL map on destroy — GCP rejects deleting a backend while
        # any URL map still references it.
        url_map = gcp.compute.URLMap(
            f"{name}-url-map",
            name=f"{name_prefix}-urlmap",
            description="Routes all traffic to the frontend GCS bucket",
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
            opts=pulumi.ResourceOptions(
                parent=self, depends_on=[backend_bucket, backend_service]
            ),
        )

        # Google-managed SSL certificate covering both domains.
        # GCP provisions and auto-renews. Free.
        # Trailing dot = fully-qualified domain name (GCP requirement).
        # Provisioning takes 10-30 minutes after DNS propagates for both domains.
        # Adding or removing a domain triggers a cert replace (not in-place update).
        ssl_cert = gcp.compute.ManagedSslCertificate(
            f"{name}-ssl-cert",
            name=f"{name_prefix}-cert-v2",  # GCP resource name kept as-is to avoid replace
            managed=gcp.compute.ManagedSslCertificateManagedArgs(
                domains=[f"{DOMAIN}.", f"{API_DOMAIN}."],
            ),
            description=f"Google-managed SSL certificate for {DOMAIN} and {API_DOMAIN}",
            opts=pulumi.ResourceOptions(
                parent=self,
                # Create the new cert before deleting the old one on future domain
                # changes — GCP rejects deleting a cert while a proxy references it.
                # aliases reconciles the Pulumi logical name as a state-only rename.
                delete_before_replace=False,
                aliases=[pulumi.Alias(name="frontend-ssl-cert-v2")],
            ),
        )

        # HTTPS proxy — terminates SSL using the managed cert.
        # depends_on url_map and ssl_cert explicitly so Pulumi deletes this proxy
        # before either of them on destroy/replace.
        https_proxy = gcp.compute.TargetHttpsProxy(
            f"{name}-https-proxy",
            name=f"{name_prefix}-https-proxy",
            url_map=url_map.self_link,
            ssl_certificates=[ssl_cert.self_link],
            opts=pulumi.ResourceOptions(parent=self, depends_on=[url_map, ssl_cert]),
        )

        # Forwarding rule — binds the static IP + port 443 to the HTTPS proxy.
        # depends_on the proxy explicitly so Pulumi deletes this rule before the
        # proxy on destroy/replace.
        gcp.compute.GlobalForwardingRule(
            f"{name}-https-rule",
            name=f"{name_prefix}-https-rule",
            ip_address=ip.address,
            ip_protocol="TCP",
            port_range="443",
            target=https_proxy.self_link,
            load_balancing_scheme="EXTERNAL",
            opts=pulumi.ResourceOptions(parent=self, depends_on=[https_proxy]),
        )

        # ── HTTP → HTTPS redirect ─────────────────────────────────────────────

        # All port 80 traffic (both domains) is redirected to HTTPS.
        redirect_url_map = gcp.compute.URLMap(
            f"{name}-redirect-url-map",
            name=f"{name_prefix}-redirect-urlmap",
            default_url_redirect=gcp.compute.URLMapDefaultUrlRedirectArgs(
                https_redirect=True,
                strip_query=False,
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        http_proxy = gcp.compute.TargetHttpProxy(
            f"{name}-http-proxy",
            name=f"{name_prefix}-http-proxy",
            url_map=redirect_url_map.self_link,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[redirect_url_map]),
        )

        gcp.compute.GlobalForwardingRule(
            f"{name}-http-rule",
            name=f"{name_prefix}-http-rule",
            ip_address=ip.address,
            ip_protocol="TCP",
            port_range="80",
            target=http_proxy.self_link,
            load_balancing_scheme="EXTERNAL",
            opts=pulumi.ResourceOptions(parent=self, depends_on=[http_proxy]),
        )

        self.url = f"https://{DOMAIN}"
        self.api_url = f"https://{API_DOMAIN}"

        self.register_outputs(
            {
                "bucket": self.bucket,
                "ip_address": self.ip_address,
                "url": self.url,
                "api_url": self.api_url,
            }
        )
