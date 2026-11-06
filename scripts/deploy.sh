#!/usr/bin/env bash
# Deploy DataOps Copilot to Azure Container Apps.
#
#   1. Create the resource group (bootstrap.bicep, subscription scope).
#   2. Deploy the platform without the app: ACR, Log Analytics, Container Apps
#      environment, Key Vault, ADLS Gen2, managed identity and RBAC.
#   3. Seed Key Vault secrets (only if missing) from ANTHROPIC_API_KEY /
#      LANGSMITH_API_KEY in the environment.
#   4. Build the image in ACR (no local Docker needed).
#   5. Deploy the Container App pointing at that image.
#
# Requires: az login, and Owner (or Contributor + User Access Administrator)
# on the subscription so the template can create role assignments.
#
# Usage: ANTHROPIC_API_KEY=... scripts/deploy.sh
#        ENABLE_LANGSMITH=true LANGSMITH_API_KEY=... scripts/deploy.sh
set -euo pipefail

cd "$(dirname "$0")/.."

RESOURCE_GROUP="${RESOURCE_GROUP:-rg-dataops-copilot-dev}"
LOCATION="${LOCATION:-westus2}"
ENABLE_LANGSMITH="${ENABLE_LANGSMITH:-false}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"

echo "==> Resource group ${RESOURCE_GROUP} (${LOCATION})"
az deployment sub create \
  --name dataops-bootstrap \
  --location "${LOCATION}" \
  --parameters infra/dev.bicepparam \
  --output none

DEPLOYER_ID="$(az ad signed-in-user show --query id --output tsv)"

deploy_platform() {
  az deployment group create \
    --name dataops-main \
    --resource-group "${RESOURCE_GROUP}" \
    --parameters infra/dev-main.bicepparam \
    --parameters deployerPrincipalId="${DEPLOYER_ID}" enableLangSmith="${ENABLE_LANGSMITH}" "$@" \
    --query properties.outputs \
    --output json
}

echo "==> Platform (without app)"
OUTPUTS="$(deploy_platform deployApp=false)"
output() { jq -r ".${1}.value" <<<"${OUTPUTS}"; }
ACR_NAME="$(output containerRegistryName)"
ACR_SERVER="$(output containerRegistryLoginServer)"
KEY_VAULT="$(output keyVaultName)"
STORAGE="$(output storageAccountName)"

seed_secret() {
  local name="$1" value="${2:-}"
  if az keyvault secret show --vault-name "${KEY_VAULT}" --name "${name}" --output none 2>/dev/null; then
    echo "    ${name}: already set"
    return
  fi
  if [[ -z "${value}" ]]; then
    echo "error: secret ${name} is missing in ${KEY_VAULT}; export it and re-run" >&2
    exit 1
  fi
  # Role assignments can take a minute to propagate after the first deploy.
  for attempt in 1 2 3 4 5 6; do
    if az keyvault secret set --vault-name "${KEY_VAULT}" --name "${name}" \
      --value "${value}" --output none 2>/dev/null; then
      echo "    ${name}: set"
      return
    fi
    echo "    waiting for Key Vault access (attempt ${attempt})..."
    sleep 20
  done
  echo "error: could not write ${name} to ${KEY_VAULT}" >&2
  exit 1
}

echo "==> Key Vault secrets (${KEY_VAULT})"
seed_secret anthropic-api-key "${ANTHROPIC_API_KEY:-}"
if [[ "${ENABLE_LANGSMITH}" == "true" ]]; then
  seed_secret langsmith-api-key "${LANGSMITH_API_KEY:-}"
fi

echo "==> Image ${ACR_SERVER}/dataops-copilot:${IMAGE_TAG}"
az acr build \
  --registry "${ACR_NAME}" \
  --image "dataops-copilot:${IMAGE_TAG}" \
  --platform linux/amd64 \
  .

echo "==> Container App"
OUTPUTS="$(deploy_platform deployApp=true containerImage="${ACR_SERVER}/dataops-copilot:${IMAGE_TAG}")"
APP_URL="$(output containerAppUrl)"

cat <<EOF

Deployed.
  API:           ${APP_URL}   (try ${APP_URL}/healthz and ${APP_URL}/docs)
  Raw data:      abfss://raw@${STORAGE}.dfs.core.windows.net/<path>.parquet
  RCA reports:   https://${STORAGE}.blob.core.windows.net/dataops/rca-reports/

Upload a batch:
  az storage blob upload --auth-mode login --account-name ${STORAGE} \\
    --container-name raw --name yellow/2026-01.parquet \\
    --file data/yellow_tripdata_2026-01.parquet
EOF
