# HTTP API and CLI

## HTTP API

Start it locally with `task run`, or `python -m dataops_copilot serve --host 0.0.0.0 --port 8000`.
FastAPI serves interactive OpenAPI docs at `/docs` and the schema at
`/openapi.json`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/healthz` | Liveness probe. Returns `{"status": "ok"}`. |
| `POST` | `/scans` | Profile a batch, detect incidents and investigate each one. |
| `POST` | `/investigations` | Investigate one incident you already have. |

The service (Spark session, Claude client, report store) is built on the first
request, so the first call is slower than later ones.

### `POST /scans`

=== "Request"

    ```json
    {
      "dataset_name": "yellow_taxi",
      "batch_id": "2026-01",
      "data_uri": "abfss://raw@<storage>.dfs.core.windows.net/yellow/2026-01.parquet",
      "investigate": true
    }
    ```

    | Field | Type | |
    | --- | --- | --- |
    | `dataset_name` | string | Used to rank history and to name report blobs. |
    | `batch_id` | string | Identifies the batch in reports. |
    | `data_uri` | string | A local path, `abfss://<container>@<account>.dfs.core.windows.net/<path>` or `https://<account>.blob.core.windows.net/<container>/<path>`. A path can be one Parquet file or a prefix holding several. |
    | `investigate` | bool, default `true` | `false` only profiles and detects, with no Claude calls. |

=== "Response"

    ```json
    {
      "dataset_name": "yellow_taxi",
      "batch_id": "2026-01",
      "quality_report": {
        "row_count": 3724889,
        "null_rates": {"passenger_count": 0.2921, "...": "..."},
        "duplicate_rate": 0.0,
        "negative_fare_rate": 0.0106,
        "invalid_trip_distance_rate": 0.0338
      },
      "incidents": [
        {"metric": "negative_fare_rate", "observed_rate": 0.0106,
         "threshold": 0.001, "affected_column": "fare_amount"}
      ],
      "reports": ["IncidentRCAReport, one per incident"]
    }
    ```

!!! warning "Long-running request"

    With `investigate: true`, a scan makes several Claude calls per incident
    and can take minutes. Use a client timeout to match, or run scans as a
    background job.

### `POST /investigations`

Runs only the investigation graph. The body is an
`IncidentInvestigationRequest`:

```json
{
  "incident": {
    "metric": "negative_fare_rate",
    "observed_rate": 0.0106,
    "threshold": 0.001,
    "affected_column": "fare_amount"
  },
  "quality_report": {
    "row_count": 3724889,
    "null_rates": {"fare_amount": 0.0, "payment_type": 0.0},
    "duplicate_rate": 0.0,
    "negative_fare_rate": 0.0106,
    "invalid_trip_distance_rate": 0.0338
  },
  "dataset_name": "yellow_taxi",
  "batch_id": "2026-01",
  "data_uri": "data/yellow_tripdata_2026-01.parquet"
}
```

The planner only sees the columns listed in `quality_report.null_rates`, so
include every column you want it to consider. If `data_uri` is omitted, every
check fails with `Could not load batch data`, and the report escalates.

The response is an `IncidentRCAReport`: the request, the `report` (see
[the report fields](demo.md#the-report)) and `completed_at`. The report is also
saved to the report store.

## CLI

```text
python -m dataops_copilot scan  --dataset NAME --batch ID --data-uri URI [--no-investigate]
python -m dataops_copilot serve [--host 127.0.0.1] [--port 8000]
```

`scan` prints the same `ScanResult` JSON as `POST /scans`.
