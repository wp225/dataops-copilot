# DataOps Copilot — Project Handoff

**Purpose:** Transfer the current repository state, design, implementation, infrastructure, known risks, and recommended next steps to the next contributor.

**Snapshot date:** 2026-10-12
**Repository:** [wp225/dataops-copilot](https://github.com/wp225/dataops-copilot)
**Current maturity:** Early-stage implementation / proof of concept. Several useful slices exist, but the end-to-end incident-response product is not yet implemented or deployable from the checked-in state.

## 1. Executive summary

DataOps Copilot is intended to profile data, detect quality anomalies, and help data engineers investigate data incidents on Azure. The current Python code contains a PySpark quality profiler, deterministic threshold-based incident detection, a local JSON history search, a Claude-backed structured planning adapter, and a two-node LangGraph that retrieves history and returns an analysis plan. A FastAPI app exposes only a health endpoint.

The Azure Bicep template describes a containerized API foundation, and a Docker image/Compose setup exists. However, the checked-in development deployment workflow is incomplete, the lockfile is absent, the application/agent is not wired into an RCA API, and the repository documentation contains unrelated job-application-assistant instructions. Do not treat the current docs or deployment workflow as a trustworthy description of a working end-to-end service.

The intended outcome is a secure, auditable, evidence-grounded service that detects quality incidents and produces useful, explainable root-cause investigations—initially read-only—with clear human escalation and a durable history of prior cases.

## 2. Product intent and ideal outcome

The project description in [pyproject.toml](pyproject.toml) and source targets an agentic data-quality and incident-response system for Azure data platforms. A reasonable target user is a data engineer or platform operator responsible for batch or lake data quality.

An ideal user workflow should eventually:

1. Read a configured dataset or batch from an approved data source.
2. Compute reproducible data-quality metrics and compare them with explicit policy.
3. Create a typed incident record for each threshold violation.
4. Investigate with relevant batch metadata and prior incidents.
5. Produce a structured plan of read-only checks, then execute only approved and constrained analyses.
6. Return a grounded RCA report with evidence, confidence, caveats, recommendations, and escalation status.
7. Persist completed cases and operational traces securely for follow-up and evaluation.
8. Be served through a documented, monitored, authenticated Azure deployment with least-privilege access.

The agent should assist decisions rather than silently mutate production data. Any future write/remediation path needs explicit authorization, a reviewed plan, scoped credentials, auditability, and a human approval boundary.

## 3. Repository layout

- [src/dataops_copilot](src/dataops_copilot): installable Python package.
  - [api.py](src/dataops_copilot/api.py): FastAPI app and `/healthz` endpoint.
  - [agent](src/dataops_copilot/agent): typed investigation contracts, LangGraph, planner/history nodes and services, and evaluation helpers.
  - [quality](src/dataops_copilot/quality): Spark metrics, quality models/policy, and incident detection.
  - [utils](src/dataops_copilot/utils): local Spark session helper.
  - [py.typed](src/dataops_copilot/py.typed): marks the package as typed.
- [tests](tests): API, agent, and quality tests; Spark tests use a shared fixture in [tests/conftest.py](tests/conftest.py).
- [infra](infra): subscription-scope resource-group bootstrap and resource-group-scope Azure deployment templates, with dev parameter files and generated output snapshots.
- [.github/workflows](.github/workflows): pull-request CI, documentation publishing, PyPI release, and dev deployment workflows.
- [evals](evals): version-controlled planner evaluation examples.
- [scripts](scripts): planner-evaluation dataset sync/run helpers and a graph-diagram generator.
- [notebooks/profiling.ipynb](notebooks/profiling.ipynb): exploratory Spark profiling notebook.
- [data](data): local sample data; this directory is ignored by Git. The current workspace contains a January 2026 yellow taxi Parquet sample, but it is not a distributable/tracked project asset.
- [docs](docs): currently inconsistent and partly unrelated documentation; see “Documentation state” below.
- [site](site): generated static-site artifacts; treat as build output, not authoritative source.
- [Dockerfile](Dockerfile) and [compose.yml](compose.yml): container build and local API runtime.
- [TODO.md](TODO.md): short existing backlog.
- [README.md](README.md), [mkdocs.yml](mkdocs.yml), [CHANGELOG.md](CHANGELOG.md), and [CITATION.cff](CITATION.cff): project metadata/docs/release support.

## 4. Implementation details

### Quality profiling and detection

- [quality/profiler.py](src/dataops_copilot/quality/profiler.py) reads Parquet through a supplied `SparkSession` and calculates row count, per-column null rates, duplicate rate, negative-fare rate, and invalid-trip-distance rate.
- Negative fares are rows where `fare_amount < 0`; invalid distances are rows where `trip_distance <= 0`. These checks are currently taxi-domain-specific and assume the relevant columns exist.
- Duplicate rate is calculated as `(row_count - distinct_row_count) / row_count`. Empty data returns zero for applicable rates.
- [quality/models.py](src/dataops_copilot/quality/models.py) validates rates in `[0, 1]`; `QualityReport` is frozen and rejects extra fields.
- [quality/policy.py](src/dataops_copilot/quality/policy.py) provides one default threshold (`0.001`).
- [quality/detector.py](src/dataops_copilot/quality/detector.py) emits incidents for rates strictly greater than the policy threshold. Equality does not trigger an incident. The detector checks null rates, duplicates, negative fares, and invalid trip distances.
- [utils/pyspark_session.py](src/dataops_copilot/utils/pyspark_session.py) creates a local Spark session using `local[2]`.

### RCA contracts and workflow

- [agent/models.py](src/dataops_copilot/agent/models.py) defines the request, historical match, hypothesis, analysis plan, generated-analysis, code-validation, execution-result, and final RCA report Pydantic models.
- [agent/state.py](src/dataops_copilot/agent/state.py) defines `InvestigationState`, including request, history, plan, future analysis/execution fields, iteration/evidence flags, and final report.
- [agent/services/history.py](src/dataops_copilot/agent/services/history.py) loads a JSON array of completed reports and returns cases with the same incident metric. It annotates same-column and same-dataset matches. This is exact-field matching, not semantic search or a ranked retrieval system.
- [agent/nodes/history.py](src/dataops_copilot/agent/nodes/history.py) wraps that local search as a LangGraph node and updates `historical_matches`.
- [agent/services/planner.py](src/dataops_copilot/agent/services/planner.py) adapts a supplied LangChain `ChatAnthropic` model to structured `AnalysisPlan` output. Its system prompt asks for hypotheses and read-only checks and prohibits code generation/data modification.
- [agent/nodes/planner.py](src/dataops_copilot/agent/nodes/planner.py) calls the injected `Planner` with the request and retrieved historical cases.
- [agent/graph.py](src/dataops_copilot/agent/graph.py) currently creates a linear graph: `START → historic_search → analysis_planning → END`. It has no investigation loop, execution, validation, or final-report assembly yet.
- [agent/service.py](src/dataops_copilot/agent/service.py) exists but is empty; there is no orchestration service currently connecting the graph to the HTTP API.

### Evaluations and experimentation

- [agent/evaluations/models.py](src/dataops_copilot/agent/evaluations/models.py) and [agent/evaluations/datasets.py](src/dataops_copilot/agent/evaluations/datasets.py) validate/load planner cases from JSON.
- [evals/rca_planner_v1.json](evals/rca_planner_v1.json) currently contains one golden example.
- [agent/evaluations/planner.py](src/dataops_copilot/agent/evaluations/planner.py) builds a LangSmith-compatible target and evaluates a heuristic for unsafe/mutating terms in a plan. This term scan is a lightweight evaluator, not a security boundary or execution sandbox.
- [scripts/sync_planner_eval_dataset.py](scripts/sync_planner_eval_dataset.py) creates the LangSmith dataset if it does not already exist; [scripts/run_planner_eval.py](scripts/run_planner_eval.py) runs a manual experiment. The runner expects `ANTHROPIC_MODEL`; the LangChain provider also requires valid Anthropic credentials. LangSmith credentials/configuration are needed for dataset and experiment calls. Do not store credentials in the repository.
- [scripts/visualize_agent_graph.py](scripts/visualize_agent_graph.py) writes a rendered graph image under `docs/diagrams/agents/` and uses IPython display utilities.

### HTTP and container runtime

- [api.py](src/dataops_copilot/api.py) creates a FastAPI app titled “DataOps Copilot” and implements `GET /healthz`, returning `{"status":"ok"}`. There are no incident submission, profiling, history, planner, or RCA routes yet.
- [Dockerfile](Dockerfile) uses a multi-stage build with the Astral uv image, installs production dependencies without dev dependencies, then runs Python 3.13 slim and starts Uvicorn on port 8000.
- [compose.yml](compose.yml) builds the local image and publishes port 8000. The basic local smoke check is `http://localhost:8000/healthz` after starting Compose.
- The runtime image does not install Java. This is fine for the current health-only API, but Spark profiling will need a deliberate runtime decision (install a compatible JRE or connect to a remote Spark service) before being exposed from the container.

## 5. Infrastructure and delivery

### Bicep design

- [infra/bootstrap.bicep](infra/bootstrap.bicep) is subscription-scoped and creates a tagged resource group.
- [infra/dev.bicepparam](infra/dev.bicepparam) supplies bootstrap values: `westus2`, `rg-dataops-copilot-dev`, and `dev`.
- [infra/main.bicep](infra/main.bicep) is resource-group-scoped and expects `environment` and an immutable `containerImage` URI.
- The main template describes Log Analytics (30-day retention), a Basic ACR with admin access disabled, a Container Apps managed environment, an RBAC-enabled standard Key Vault, a user-assigned managed identity, an ACR pull role assignment for that identity, and an externally accessible Container App.
- The Container App uses HTTPS ingress targeting port 8000, probes `/healthz`, scales from zero to two replicas, and uses 0.25 CPU / 0.5 GiB memory. The template outputs ACR login server, environment ID, Key Vault URI, app name, and app URL.
- [infra/dev-main.bicepparam](infra/dev-main.bicepparam) supplies only `environment = 'dev'`; it does not supply the required `containerImage`. A deployment process must inject an immutable image URI when invoking the main template.
- [infra/outputs](infra/outputs) contains generated deployment-template JSON snapshots. They are not the source of truth and may be stale relative to the Bicep source.

### Current deployment blocker

[.github/workflows/deploy-dev.yml](.github/workflows/deploy-dev.yml) is incomplete in the checked-in content: the Azure login step ends mid-configuration (`df`) and there are no complete build/push, Bicep deployment, or app rollout steps. Treat it as a stub, not an operational deployment pipeline. Before relying on it, complete and validate:

1. Azure federated OIDC login values and GitHub `dev` environment configuration (tenant, subscription, client ID, and federated credential / permissions).
2. Bootstrap/resource-group creation and resource deployment sequencing.
3. Container build, ACR authentication, push of an immutable tag/digest, and passing that URI as `containerImage`.
4. Deployment outputs, health verification, failure handling, and least-privilege identity assignments.
5. Whether Key Vault is needed now; no current app configuration references its URI or grants the app identity secret permissions.

The workflow currently requests `id-token: write`, but that alone does not configure Azure OIDC. No credentials should be committed.

### CI, docs, and package release

- [.github/workflows/pull-request.yml](.github/workflows/pull-request.yml) runs on PRs and pushes to `main`, with Python 3.13/3.14. It installs with `uv sync --locked`, runs Ruff lint/format checks, `ty check`, pytest, coverage, `uv audit`, and `zizmor` workflow analysis.
- Coverage is configured with an 85% minimum in [pyproject.toml](pyproject.toml). Spark-based tests need a compatible local Java runtime; the notebook has a developer-specific Homebrew JDK 21 path that should not be copied into general setup instructions.
- [.github/workflows/docs.yml](.github/workflows/docs.yml) builds the documentation using `uv run zensical build --clean` and publishes the generated `site` directory to GitHub Pages.
- [.github/workflows/pypi-publish.yml](.github/workflows/pypi-publish.yml) is configured for semantic-release on `main` and a tag-triggered PyPI publish using Trusted Publishing and attestations. Verify the PyPI trusted-publisher settings and release workflow before relying on publication.
- `pyproject.toml` requires Python `>=3.13,<4`; dependencies include FastAPI, Pydantic, PySpark 4.2.x, LangChain/LangGraph, Anthropic/OpenAI integrations, LangSmith, Azure Core, and development tooling.
- **Lockfile issue:** no `uv.lock` is present in the workspace/file search, but CI and Docker use `uv sync --locked` / `uv sync --frozen`, and semantic-release is configured to regenerate and commit `uv.lock`. Generate and check in a lockfile (and ensure `.gitignore` does not exclude it) before expecting clean CI, Docker builds, or releases.

## 6. What is done versus incomplete

### Implemented

- Typed quality-report, incident, request, planning, execution, and final-report contracts.
- Spark metric calculation for the current taxi-oriented checks.
- Deterministic policy threshold detector.
- Local JSON historical-case lookup and a history graph node.
- Claude structured-output planning adapter with injected planner interface.
- A working-shaped linear LangGraph for history lookup followed by planning, with unit/integration coverage in [tests/agent](tests/agent).
- Planner evaluation target, read-only-term evaluator, one local example, and scripts for LangSmith dataset/evaluation operations.
- FastAPI health endpoint, container image definition, Compose file, and Bicep resource definitions.
- CI, docs publishing, and package publishing workflow definitions (subject to the lockfile and docs caveats in this handoff).

### Not implemented or not verified as operational

- An end-to-end API contract or service that accepts an incident, loads data, runs the graph, and returns a final RCA.
- A production data-source abstraction, authorization model, or configurable metric catalog; profiling is currently taxi-schema-specific.
- Azure deployment automation, image build/push/release, production environment setup, or post-deploy verification.
- Safe constrained analysis execution, sandboxing, SQL/Python allowlists, resource limits, and approval workflow. The models anticipate these stages, but the graph does not implement them.
- Investigation loop, evidence sufficiency logic, final report assembly, durable storage, history retention/search quality, and ADLS integration.
- Sufficient evaluation breadth and quality gates for planner accuracy, evidence coverage, calibration, escalation, and safe behavior. Current LangSmith scoring only scans for a short list of mutation terms.
- Current, accurate user/developer docs and a working documented app entrypoint.
- Verified status of the latest CI, release, Azure deployment, or runtime behavior. This handoff records source inspection, not a successful build/test/deploy.

## 7. Priority backlog

### P0 — Make the repository reliable and truthful

1. Generate and commit `uv.lock`; correct ignore rules if necessary and verify `uv sync --locked`, the Docker build, and CI.
2. Repair `.github/workflows/deploy-dev.yml` and test Bicep deployment parameters/outputs. Avoid publishing mutable `latest`-only image references; pin by commit or digest.
3. Replace the unrelated candidate/job-search material in [docs/index.md](docs/index.md) and [docs/setup.md](docs/setup.md); correct [docs/getting-started.md](docs/getting-started.md) and [README.md](README.md) to match the actual package. The README’s `task run` target references a `dataops_copilot.py` file that is absent, and its documented `task docs` / `task serve` tasks are not declared in `pyproject.toml`.
4. Add a concise real quickstart, current environment requirements (including Java for Spark), actual app command, and explicit statement of what the service currently does.

### P1 — Deliver the first usable end-to-end RCA slice

1. Define and validate the incident ingestion/API contract and response/error semantics.
2. Add settings/configuration and dependency-injection for data source, policy, model, and history repository.
3. Implement an orchestration service and wire it to the graph/API; add integration tests without live model credentials.
4. Finish report assembly and return evidence, plan, history references, confidence/caveats, and escalation recommendations.
5. Improve the planner evaluation dataset and evaluator to assess cause categories, required checks, evidence grounding, escalation, and regressions—not just mutation words.

### P2 — Safe analysis and durable operations

1. Decide whether analyses are generated SQL, fixed query templates, or another restricted interface. Prefer constrained, parameterized, read-only operations over arbitrary generated code.
2. If execution is needed, implement static validation plus an isolated runtime, read-only credentials, table/column allowlists, query/time/row limits, timeouts, audit logs, and explicit failure handling. A prompt or string-matching evaluator is not sufficient protection.
3. Replace local JSON history with a repository interface and durable Azure storage (the existing TODO specifically calls out ADLS); define schema versioning, retention, access control, and migrations.
4. Add observability, tracing policy, privacy controls, health/readiness semantics, authentication/authorization, rate limits, and operational alerts before production exposure.
5. Generalize quality rules beyond taxi-specific field names and test empty, malformed, large, and schema-drift inputs.

## 8. Local development and validation

### Prerequisites

- `uv` (CI currently pins 0.11.15); Python 3.13 or 3.14 per project/CI configuration.
- A compatible Java runtime for PySpark tests and local profiling; configure `JAVA_HOME` for the local machine. Do not use the notebook’s machine-specific absolute JDK path as a portable default.
- Anthropic API credentials and `ANTHROPIC_MODEL` only for live planner use. LangSmith credentials/configuration are needed only for LangSmith dataset/evaluation scripts.

### Install and run

- Install/sync the project: `uv sync`.
- Run tests: `uv run pytest tests`.
- Lint: `uv run ruff check .`.
- Check formatting: `uv run ruff format --check .`.
- Type-check: `uv run ty check`.
- Check coverage: `uv run coverage run -m pytest tests && uv run coverage report`.
- Run local API: `uv run uvicorn dataops_copilot.api:app --host 0.0.0.0 --port 8000`.
- Run container locally: `docker compose up --build`; then request `/healthz` on port 8000.

The CI/release/Docker locked-install flows cannot be considered reproducible until `uv.lock` is restored. Live model and LangSmith operations incur external service/configuration requirements; unit tests should continue to inject fakes and avoid network access.

## 9. Risks and handoff notes

- **Documentation confusion:** documentation currently describes candidate profiles, scraping job boards, and applications—unrelated to the Python package and Azure DataOps product. Treat those instructions as stale/copy-pasted; do not follow the `/setup` workflow.
- **Deployment is not ready:** the dev workflow is truncated and does not deploy the defined infrastructure or image.
- **No lockfile:** reproducible dependency installation paths currently reference a missing lockfile.
- **API is a health-only shell:** successful `/healthz` does not mean Spark, the planner, Azure access, or RCA is functioning.
- **Safety gap:** “read-only” is currently a planner prompt intent and an evaluation heuristic. There is no executable analysis stage or technical enforcement boundary.
- **Data locality:** `/data` is ignored and the local taxi sample is not version-controlled. Avoid placing real/customer data in Git, container layers, logs, test fixtures, or hosted evaluation inputs without an approved privacy/security policy.
- **Azure exposure:** Bicep configures external ingress. Add authentication and network/security controls before using non-demo data.
- **Secrets/identity:** Key Vault and managed identity resources are declared, but application secret loading and Key Vault RBAC are not implemented. Use GitHub OIDC and managed identity rather than long-lived credentials where possible.
- **Metric assumptions:** the profiler will fail or mislead when taxi fields are missing or have unexpected types; make metrics schema-aware before broadening data sources.
- **No successful verification claimed:** no tests, builds, or Azure deployments were run while preparing this handoff.

## 10. Existing backlog and references

The existing [TODO.md](TODO.md) calls out RCA input/output models, local history search, restricted analysis execution, an investigation loop, LangSmith tracing/evaluation, and moving history from local files to ADLS. The models, history lookup, planner evaluation scaffolding, and initial graph now exist in part; the safe execution, graph loop, tracing improvements, and durable ADLS history remain open. Update that file alongside future implementation so it stays aligned with this handoff.

Key starting points:

- [Quality profiler](src/dataops_copilot/quality/profiler.py)
- [Incident detector](src/dataops_copilot/quality/detector.py)
- [Investigation contracts](src/dataops_copilot/agent/models.py)
- [Investigation graph](src/dataops_copilot/agent/graph.py)
- [Planner adapter](src/dataops_copilot/agent/services/planner.py)
- [Bicep app deployment](infra/main.bicep)
- [Dev deployment workflow](.github/workflows/deploy-dev.yml)
- [CI workflow](.github/workflows/pull-request.yml)
