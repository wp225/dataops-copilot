# Deployment (Azure Container Apps)

`scripts/deploy.sh` deploys everything from an `az login` session. No local
Docker is needed because the image is built in Azure Container Registry.

```bash
ANTHROPIC_API_KEY=sk-ant-... scripts/deploy.sh
# with LangSmith tracing:
ENABLE_LANGSMITH=true LANGSMITH_API_KEY=... ANTHROPIC_API_KEY=... scripts/deploy.sh
```

The script runs in two phases because Container Apps resolves Key Vault secret
references when a revision is created:

1. `infra/bootstrap.bicep` creates the resource group.
2. `infra/main.bicep` with `deployApp=false` creates the platform:
   - Azure Container Registry, Log Analytics and the Container Apps environment
   - Key Vault (RBAC mode)
   - ADLS Gen2 storage (hierarchical namespace, no shared keys, no public blobs)
     with containers `raw` (input batches) and `dataops` (RCA reports)
   - a user-assigned managed identity with `AcrPull`, `Storage Blob Data
     Contributor` and `Key Vault Secrets User`
   - for the signed-in deployer, `Key Vault Secrets Officer` and `Storage Blob
     Data Contributor`
3. The script seeds `anthropic-api-key` (and `langsmith-api-key`) in Key Vault
   if they are missing.
4. `az acr build` builds `dataops-copilot:<git sha>`.
5. `main.bicep` with `deployApp=true` creates the Container App (2 vCPU, 4 GiB,
   scale 0 to 1). It authenticates to ACR, Key Vault and storage with the
   managed identity, and stores reports in ADLS (`DATAOPS_REPORT_STORE=adls`).

Your account needs Owner, or Contributor plus User Access Administrator, on
the subscription, because the template creates role assignments.

## Running a scan in Azure

```bash
az storage blob upload --auth-mode login --account-name <storage> \
  --container-name raw --name yellow/2026-01.parquet \
  --file data/yellow_tripdata_2026-01.parquet

curl -X POST "$APP_URL/scans" -H 'content-type: application/json' -d '{
  "dataset_name": "yellow_taxi",
  "batch_id": "2026-01",
  "data_uri": "abfss://raw@<storage>.dfs.core.windows.net/yellow/2026-01.parquet"
}'
```

Reports land at `dataops/rca-reports/<metric>/<dataset>/<batch>/<timestamp>.json`,
and later investigations of the same metric retrieve them as history.

A scan runs one investigation per incident, each making several Claude calls,
so it can take minutes. For large or frequent batches, move scans to a
background job (Container Apps Jobs) instead of a synchronous HTTP request.
