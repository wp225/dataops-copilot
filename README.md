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
# run src/dataops_copilot/dataops_copilot.py
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
