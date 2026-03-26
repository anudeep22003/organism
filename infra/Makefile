STACK       := dev
PROJECT     := shared-apps-infrastructure
REGION      := europe-west2
REGISTRY    := $(REGION)-docker.pkg.dev/$(PROJECT)/storyengine-dev
IMAGE       := $(REGISTRY)/backend
BACKEND_DIR := $(shell git rev-parse --show-toplevel)/backend

# The git SHA of HEAD in the backend directory.
# Using the monorepo root SHA keeps image tags consistent across all
# components — one SHA per commit, no per-subdirectory confusion.
SHA := $(shell git rev-parse --short HEAD)

# ── Pulumi ────────────────────────────────────────────────────────────────────

.PHONY: preview
preview:
	PULUMI_CONFIG_PASSPHRASE="" pulumi preview --stack $(STACK)

.PHONY: up
up:
	PULUMI_CONFIG_PASSPHRASE="" pulumi up --stack $(STACK)

.PHONY: outputs
outputs:
	PULUMI_CONFIG_PASSPHRASE="" pulumi stack output --stack $(STACK)

# ── Docker ────────────────────────────────────────────────────────────────────

.PHONY: build
build:
	docker build --platform linux/amd64 \
		-t $(IMAGE):$(SHA) \
		$(BACKEND_DIR)

.PHONY: push
push:
	docker push $(IMAGE):$(SHA)

# ── Deploy ────────────────────────────────────────────────────────────────────

# build-and-deploy: build the image, push it, stamp the SHA into Pulumi config,
# then run pulumi up — all in one command. The SHA is always the current HEAD,
# so the running revision is always traceable to an exact commit.
.PHONY: deploy
deploy: build push
	PULUMI_CONFIG_PASSPHRASE="" pulumi config set image_tag $(SHA) --stack $(STACK)
	PULUMI_CONFIG_PASSPHRASE="" pulumi up --stack $(STACK)

# ── Secrets ───────────────────────────────────────────────────────────────────

.PHONY: populate-secrets
populate-secrets:
	bash scripts/populate-secrets.sh
