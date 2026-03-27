import pulumi_gcp as gcp

_REGION = "europe-west2"

# Subnet CIDR for our resources (Cloud Run direct VPC egress, future VMs).
# 10.0.0.0/20 = 4096 addresses. Plenty for dev.
_SUBNET_CIDR = "10.0.0.0/20"

# Reserved range for Google-managed services (Cloud SQL, Memorystore etc).
# This block is allocated inside our VPC's address space but the actual
# machines live in Google's network — peering stitches them together.
# /16 = 65536 addresses, giving Google room to assign IPs to managed instances.
_SERVICES_CIDR_BASE = "10.1.0.0"
_SERVICES_CIDR_PREFIX = 16


def create_network() -> tuple[
    gcp.compute.Network, gcp.compute.Subnetwork, gcp.servicenetworking.Connection
]:
    """
    Creates the VPC and subnet for the storyengine dev environment.

    VPC (Virtual Private Cloud): the private network that owns all our
    resources. It is global — it spans all regions. auto_create_subnetworks
    is disabled so we define subnets explicitly rather than getting one
    per region automatically.

    Subnet: a regional slice of the VPC with a specific IP range. Resources
    that need VPC membership (Cloud Run via direct egress, future VMs) get
    IPs from this range.

    private_ip_google_access: allows instances in the subnet to reach Google
    APIs (Secret Manager, GCS, Artifact Registry) using their private Google
    IP ranges rather than going out to the public internet. Without this,
    Cloud Run would need a NAT gateway to call Google APIs.

    Private services access (the peering to Google's managed services network):
    we reserve a /16 block and create a servicenetworking.Connection.
    This is what allows Cloud SQL to get a private IP reachable from our subnet.
    The peering must exist before Cloud SQL is created — Pulumi handles this
    ordering via the depends_on on the Connection resource.
    """
    vpc = gcp.compute.Network(
        "vpc",
        name="storyengine-dev-vpc",
        auto_create_subnetworks=False,
        description="StoryEngine dev VPC",
    )

    subnet = gcp.compute.Subnetwork(
        "subnet",
        name="storyengine-dev-subnet",
        region=_REGION,
        ip_cidr_range=_SUBNET_CIDR,
        network=vpc.id,
        # Allows Cloud Run (via VPC egress) to reach Google APIs privately.
        private_ip_google_access=True,
    )

    # Reserve a block of IP addresses within our VPC's address space for
    # Google's managed services. The block is "ours" on paper but Google
    # assigns it to managed service instances (Cloud SQL, Memorystore etc).
    # purpose=VPC_PEERING signals this is for private services access.
    reserved_range = gcp.compute.GlobalAddress(
        "private-services-range",
        name="storyengine-dev-private-services",
        purpose="VPC_PEERING",
        address_type="INTERNAL",
        prefix_length=_SERVICES_CIDR_PREFIX,
        address=_SERVICES_CIDR_BASE,
        network=vpc.id,
    )

    # Create the peering connection between our VPC and Google's managed
    # services network. This is what makes Cloud SQL's private IP routable
    # from our subnet. The connection uses the reserved range above as the
    # address space for Google's side of the peering.
    #
    # This resource is slow to create (~2 minutes) and must complete before
    # Cloud SQL is provisioned. We return it explicitly so database.py can
    # declare a depends_on — without this Pulumi runs them in parallel and
    # Cloud SQL fails because the peering doesn't exist yet.
    peering_connection = gcp.servicenetworking.Connection(
        "private-services-connection",
        network=vpc.id,
        service="servicenetworking.googleapis.com",
        reserved_peering_ranges=[reserved_range.name],
    )

    return vpc, subnet, peering_connection
