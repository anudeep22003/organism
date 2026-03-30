"""
VPC networking component.

Creates the VPC, subnet, and private services peering connection needed
for Cloud SQL private IP and Cloud Run VPC egress.

Usage:
    network = Network("network")
    # Access resources:
    network.vpc               # gcp.compute.Network
    network.subnet            # gcp.compute.Subnetwork
    network.peering_connection  # gcp.servicenetworking.Connection

Attributes exposed:
    vpc               (gcp.compute.Network): the VPC
    subnet            (gcp.compute.Subnetwork): the regional subnet (10.0.0.0/20)
    peering_connection (gcp.servicenetworking.Connection): the private services
                      peering that makes Cloud SQL's private IP reachable

Design decisions:
    - auto_create_subnetworks=False: we define subnets explicitly rather than
      getting one per region automatically. Cleaner and more intentional.
    - private_ip_google_access=True on the subnet: Cloud Run containers can
      reach Google APIs (Secret Manager, GCS, Artifact Registry) using private
      Google IP ranges. Without this, Cloud Run would need a NAT gateway.
    - The /16 reserved range gives Google 65536 addresses to assign to managed
      service instances (Cloud SQL, Memorystore etc).
    - peering_connection is exposed so database.py can declare depends_on —
      Cloud SQL creation fails if peering doesn't exist yet, and Pulumi can't
      infer this dependency from the SQL instance arguments alone.
    - reserved_range is internal to this component — nothing outside needs it.

Constructor args (all optional):
    subnet_cidr   (str): CIDR for the regional subnet. Default "10.0.0.0/20"
                         (4096 addresses). Override if this range conflicts with
                         a VPN or existing peered network.
    services_cidr (str): CIDR reserved for Google-managed services (Cloud SQL,
                         Memorystore etc). Default "10.1.0.0/16" (65536 addresses).
                         Must not overlap with subnet_cidr or any peered networks.

Dependency note:
    Pass network.peering_connection in depends_on when creating any resource
    that needs the private services network (Cloud SQL, Memorystore, etc.):

        db = Database("db", vpc=network.vpc, peering=network.peering_connection, ...)
"""

import pulumi
import pulumi_gcp as gcp

from components.config import APP, REGION, resource_name  # APP used in type identifier


class Network(pulumi.ComponentResource):
    """
    VPC, subnet, and private services peering for the app stack.

    Creates three GCP resources:
    - A global VPC (the private network that owns all resources)
    - A regional subnet (where Cloud Run containers get their VPC IPs)
    - A private services peering connection (makes Cloud SQL private IP routable)

    The peering connection is slow to create (~2 minutes). It must exist before
    any Cloud SQL instance is provisioned. Pass peering_connection in depends_on
    when creating stateful resources that need the private services network.

    Child resources (all parented to this component):
        {name}-vpc                      gcp.compute.Network
        {name}-subnet                   gcp.compute.Subnetwork
        {name}-private-services-range   gcp.compute.GlobalAddress  (internal)
        {name}-peering-connection       gcp.servicenetworking.Connection
    """

    vpc: gcp.compute.Network
    subnet: gcp.compute.Subnetwork
    peering_connection: gcp.servicenetworking.Connection

    def __init__(
        self,
        name: str,
        subnet_cidr: str = "10.0.0.0/20",
        services_cidr: str = "10.1.0.0/16",
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(f"{APP}:infra:Network", name, {}, opts)

        # Split the services CIDR string into base address and prefix length.
        # e.g. "10.1.0.0/16" → address="10.1.0.0", prefix_length=16
        _services_cidr_base, _services_cidr_prefix_str = services_cidr.split("/")
        _services_cidr_prefix = int(_services_cidr_prefix_str)

        # VPC: the private network that owns all our resources.
        # Global — it spans all regions. auto_create_subnetworks disabled
        # so we define subnets explicitly.
        self.vpc = gcp.compute.Network(
            f"{name}-vpc",
            name=resource_name("vpc"),
            auto_create_subnetworks=False,
            description="StoryEngine dev VPC",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Subnet: a regional slice of the VPC. Resources that need VPC
        # membership (Cloud Run via direct egress, future VMs) get IPs here.
        self.subnet = gcp.compute.Subnetwork(
            f"{name}-subnet",
            name=resource_name("subnet"),
            region=REGION,
            ip_cidr_range=subnet_cidr,
            network=self.vpc.id,
            # Allows Cloud Run (via VPC egress) to reach Google APIs privately
            # without a NAT gateway.
            private_ip_google_access=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Reserve a block of IP addresses within our VPC's address space for
        # Google's managed services. The block is "ours" on paper but Google
        # assigns it to managed service instances (Cloud SQL, Memorystore etc).
        # purpose=VPC_PEERING signals this is for private services access.
        reserved_range = gcp.compute.GlobalAddress(
            f"{name}-private-services-range",
            name=resource_name("private-services"),
            purpose="VPC_PEERING",
            address_type="INTERNAL",
            prefix_length=_services_cidr_prefix,
            address=_services_cidr_base,
            network=self.vpc.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Peering connection between our VPC and Google's managed services
        # network. This is what makes Cloud SQL's private IP routable from
        # our subnet. Must complete before Cloud SQL is provisioned.
        # Returned explicitly so callers can declare depends_on.
        self.peering_connection = gcp.servicenetworking.Connection(
            f"{name}-peering-connection",
            network=self.vpc.id,
            service="servicenetworking.googleapis.com",
            reserved_peering_ranges=[reserved_range.name],
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "vpc": self.vpc,
                "subnet": self.subnet,
                "peering_connection": self.peering_connection,
            }
        )
