# Configuration

Settings are read from environment variables with the `DATAOPS_` prefix, or
from a `.env` file in the working directory. Variables already set in the
environment take precedence over `.env`.

## Application settings

| Variable | Default | |
| --- | --- | --- |
| `DATAOPS_ANTHROPIC_MODEL` | `claude-opus-5-5` | Claude model for the planner, assessor and report writer. |
| `DATAOPS_ANTHROPIC_EFFORT` | `medium` | `low`, `medium`, `high`, `xhigh` or `max`. Higher effort is slower and costs more. |
| `DATAOPS_MAX_ITERATIONS` | `3` | Maximum plan, check and assess rounds per investigation. |
| `DATAOPS_QUALITY_THRESHOLD_RATE` | `0.001` | A rate above this raises an incident (0.1%). |
| `DATAOPS_REPORT_STORE` | `local` | `local` (JSON file) or `adls`. |
| `DATAOPS_LOCAL_REPORT_PATH` | `data/rca_reports.json` | Report file for the local store. |
| `DATAOPS_ADLS_ACCOUNT_URL` | none | For example `https://<account>.blob.core.windows.net`. Required when the store is `adls`. |
| `DATAOPS_ADLS_CONTAINER` | `dataops` | Container that holds `rca-reports/`. |
| `DATAOPS_DATA_CACHE_DIR` | `<system temp>/dataops-copilot` | Where remote Parquet is downloaded and cached. |
| `DATAOPS_SPARK_APP_NAME` | `dataops-copilot` | Spark application name. |

## Credentials

These are read by the client libraries, not by `Settings`:

| Variable | Used by |
| --- | --- |
| `ANTHROPIC_API_KEY` | Claude calls. Required for investigations. |
| `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT` | Optional tracing of every graph run, and the planner evaluations. |

Azure access uses `DefaultAzureCredential`: your `az login` session locally,
and the managed identity in Azure Container Apps. No storage keys are used.

!!! danger "Keep `.env` out of git"

    `.env` is ignored by git. In Azure, the API keys live in Key Vault and
    reach the container as secret references. See
    [Deploy to Azure](deployment.md).
