# :rocket: dataops-copilot

DataOps Copilot: an agentic data-quality and incident-response system for an Azure data lake.

## Setup Dev Environment

Installation is using [UV](https://docs.astral.sh/uv/) to manage everything.

**Step 1**: Create a virtual environment

```bash
uv venv
```

**Step 2**: Activate your new environment

```bash
# on windows
.venv\Scripts\activate

# on mac / linux
source .venv/bin/activate
```

**Step 3**: Install all the cool dependencies

```bash
uv sync
```

## What it does

1. **Profile** a Parquet batch with Spark (null, duplicate, negative-fare and invalid-distance rates).
2. **Detect** incidents that break the quality policy.
3. **Investigate** each incident with a LangGraph loop. Claude plans hypotheses, a fixed catalog
   of read-only Spark checks gathers evidence, Claude judges it, and the loop replans until the
   evidence is sufficient or the round cap is hit.
4. **Report** an advisory RCA that escalates to a human when evidence is insufficient, and store
   it (local JSON or ADLS) as history for future investigations.

See [docs/architecture.md](docs/architecture.md) and [docs/deployment.md](docs/deployment.md).

## Running locally

Copy `.example.env` to `.env` and set `ANTHROPIC_API_KEY`. Spark needs Java 17 or 21.

```bash
# Profile a batch and investigate every incident (prints JSON)
uv run python -m dataops_copilot scan --dataset yellow_taxi --batch 2026-01 \
  --data-uri data/yellow_tripdata_2026-01.parquet

# Only profile and detect (no Claude calls)
uv run python -m dataops_copilot scan --dataset yellow_taxi --batch 2026-01 \
  --data-uri data/yellow_tripdata_2026-01.parquet --no-investigate

# HTTP API on http://127.0.0.1:8000 (POST /scans, POST /investigations, GET /docs)
task run
```

## Tests

`task tests` skips tests that need a JVM. They're marked `spark` automatically
when they use the `spark` fixture. Run them on their own, serially:

```bash
uv run pytest -m spark -p no:xdist
```

## Deploying to Azure

```bash
ANTHROPIC_API_KEY=sk-ant-... scripts/deploy.sh
```

## Github Repo Setup

To add your new project to its Github repository, firstly make sure you have created a project named **dataops-copilot** on Github.
Follow these steps to push your new project.

```bash
git remote add origin git@github.com:wp225/dataops-copilot.git
git branch -M main
git push -u origin main
```

## Built-in CLI Commands

We've included a bunch of useful CLI commands for common project tasks using [taskipy](https://github.com/taskipy/taskipy).

```bash
# run the HTTP API locally
task run

# run all tests
task tests

# run test coverage and generate report
task coverage

# typechecking with Ty
task type

# ruff linting
task lint

# format with ruff
task format

# build/serve docs
task docs
task serve
```

## PyPI Deployment

This project uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) — no API tokens required.

1. On [PyPI](https://pypi.org/), open your project's settings and add a trusted publisher for this repository:
   - Workflow name: `pypi-publish.yml`
   - Environment: `pypi`
   - Repository: `<owner>/dataops-copilot`
2. Push commits to `main` — [python-semantic-release](https://python-semantic-release.readthedocs.io/) bumps the version, updates the changelog, and creates a `v*.*.*` tag automatically.
3. The tag triggers the publish workflow, which builds the package, generates [PEP 740 attestations](https://peps.python.org/pep-0740/), and uploads to PyPI.

## Dependabot Setup

1. Go to the "Settings -> Advanced Security" tab in your repository.
2. Under the "Dependabot" section enable the options you want to monitor, we recommend the "Dependabot security updates" at the minimum.

Dependabot is configured to do _weekly_ scans of your dependencies, and pull requests will be prefixed with "DBOT". These settings can be adjusted in the `./.github/dependabot.yml` file.

## References

- [Pattern](https://github.com/wyattferguson/pattern) - A modern cookiecutter template for your next Python project.

## License

MIT

## Contact

Created by [Jeorge Joshi](https://github.com/wp225)
