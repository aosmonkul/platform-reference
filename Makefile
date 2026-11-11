CLUSTER ?= platform
IMAGE   ?= hello:local
ARGOCD_CHART_VERSION ?= 10.18.0

.PHONY: help test lint up image deploy smoke argocd down

help: ## Show the available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

test: ## Run the app's unit tests
	cd app && python -m unittest -v

lint: ## Lint the app and the chart
	cd app && ruff check . && ruff format --check .
	helm lint deploy/chart --strict

up: ## Create a local kind cluster
	kind create cluster --name $(CLUSTER)

image: ## Build the image and load it into kind
	docker build -t $(IMAGE) app
	kind load docker-image $(IMAGE) --name $(CLUSTER)

deploy: image ## Install the chart straight from the working tree
	helm upgrade --install hello deploy/chart \
		--namespace hello --create-namespace \
		--set image.repository=$(firstword $(subst :, ,$(IMAGE))) \
		--set image.tag=$(lastword $(subst :, ,$(IMAGE))) \
		--wait --timeout 3m

smoke: ## Check the running service
	./scripts/smoke.sh hello

argocd: ## Install Argo CD and hand the cluster over to Git
	helm repo add argo https://argoproj.github.io/argo-helm
	helm upgrade --install argocd argo/argo-cd --version $(ARGOCD_CHART_VERSION) \
		--namespace argocd --create-namespace --wait
	kubectl apply -f gitops/bootstrap/root.yaml

down: ## Delete the kind cluster
	kind delete cluster --name $(CLUSTER)
