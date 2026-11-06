# Development

## Tasks

Tasks run with [taskipy](https://github.com/taskipy/taskipy) inside the uv
environment (`uv run task <name>`):

| Task | Does |
| --- | --- |
| `task run` | Run the HTTP API on `127.0.0.1:8000`. |
| `task tests` | Run the test suite. |
| `task coverage` | Run tests with coverage (85% gate). |
| `task lint` | Lint and auto-fix with Ruff. |
| `task format` | Format with Ruff. |
| `task type` | Typecheck with ty. |
| `task docs` | Build this site with Zensical into `site/`. |
| `task serve` | Serve this site locally with live reload. |
| `task upgrade` | Upgrade all dependencies. |

## Project layout

```text
src/dataops_copilot/
  __main__.py            # CLI: scan | serve
  api.py                 # FastAPI app
  config.py              # DATAOPS_* settings
  quality/               # profiler, policy, detector, models
  agent/
    graph.py             # LangGraph wiring
    state.py             # InvestigationState
    models.py            # requests, plans, assessments, reports
    service.py           # InvestigationService, scan orchestration
    nodes/               # history, planner, run_checks, assess, report
    checks/              # read-only check catalog
    services/            # Claude calls, data loader, report store, history search
    evaluations/         # LangSmith planner target and evaluators
evals/                   # golden planner cases
infra/                   # Bicep for Azure
scripts/                 # deploy, evals, graph visualization
tests/
```

## Tests

`task tests` skips tests that need a JVM. A test that uses the `spark`
fixture is marked `spark` automatically and deselected by default. Run those
separately and serially:

```bash
uv run pytest -m spark -p no:xdist
```

Every other test, including the full investigation graph, runs without Spark,
network access or an API key: the graph takes its planner, assessor, report
writer, loader and store as injected callables.

## Continuous integration

Every pull request runs, on Python 3.13 and 3.14:

1. Ruff lint and format check
2. ty typecheck
3. pytest (parallel, with `-n auto`) and coverage (`fail_under = 85`)
4. `uv audit` for known vulnerabilities in dependencies
5. [zizmor](https://github.com/zizmorcore/zizmor) for the GitHub workflows

Pushes to `main` build this site with Zensical and publish it to GitHub Pages.

## Writing docs

The site lives in `docs/` and is configured in `mkdocs.yml`, which
[Zensical](https://zensical.org/) reads directly. Diagrams are Mermaid code
blocks, so they stay in sync with the code in review.

```bash
task serve   # http://127.0.0.1:8000
```
