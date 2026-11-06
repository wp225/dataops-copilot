# Getting started

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.11 or later.
  uv installs Python 3.13 for you.
- Java 17 or 21 for Spark (for example, `brew install openjdk@21` on macOS).
- An [Anthropic API key](https://console.anthropic.com/) for investigations.
  Profiling and detection work without one.
- Optional: a [LangSmith](https://smith.langchain.com/) key for tracing and
  planner evaluations.

## Install

```bash
git clone https://github.com/wp225/dataops-copilot.git
cd dataops-copilot
uv sync
```

## Configure

```bash
cp .example.env .env
```

Set `ANTHROPIC_API_KEY` in `.env`. Every other setting has a default; see
[Configuration](configuration.md). The `.env` file is loaded at startup, and
variables already set in your shell take precedence.

## Get a batch

Download a monthly yellow-taxi Parquet file from the
[TLC trip record page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
into `data/`, for example `data/yellow_tripdata_2026-01.parquet`. Any Parquet
file with the same columns works.

## Run a scan

=== "Profile only"

    No Claude calls. Prints the quality report and the incidents.

    ```bash
    uv run python -m dataops_copilot scan \
      --dataset yellow_taxi --batch 2026-01 \
      --data-uri data/yellow_tripdata_2026-01.parquet \
      --no-investigate
    ```

=== "Profile and investigate"

    Runs one investigation per incident and saves the reports to
    `data/rca_reports.json`.

    ```bash
    uv run python -m dataops_copilot scan \
      --dataset yellow_taxi --batch 2026-01 \
      --data-uri data/yellow_tripdata_2026-01.parquet
    ```

!!! tip "Cost and time"

    Each investigation makes at least three Claude calls (plan, assess,
    write) and up to seven with the default cap of three rounds. A batch with
    seven incidents can take a few minutes. Lower `DATAOPS_ANTHROPIC_EFFORT`
    or `DATAOPS_MAX_ITERATIONS` while you experiment.

## Run the API

```bash
task run
```

The API listens on `http://127.0.0.1:8000`, with interactive OpenAPI docs at
[`/docs`](http://127.0.0.1:8000/docs). See [HTTP API and CLI](api.md).

## Next steps

- Walk through real results in the [demo](demo.md).
- Learn how the [investigation loop](architecture.md) works.
- [Deploy to Azure](deployment.md) with one script.
