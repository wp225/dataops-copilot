"""Node that executes the planned catalog checks against the batch data."""

from collections.abc import Callable

from dataops_copilot.agent.checks.catalog import run_check
from dataops_copilot.agent.checks.models import CheckResult, PlannedCheck
from dataops_copilot.agent.services.data_loader import DataLoader
from dataops_copilot.agent.state import InvestigationState

StateUpdate = dict[str, object]


def _result_key(result: CheckResult) -> tuple[str, str | None, str | None, str | None]:
    params = result.params
    condition = params.get("condition")
    if result.check_name == "breakdown_by" and condition is None:
        condition = "negative"
    return (result.check_name, params.get("column"), params.get("group_by"), condition)


def _planned_key(check: PlannedCheck) -> tuple[str, str | None, str | None, str | None]:
    condition = check.condition
    if check.check_name == "breakdown_by" and condition is None:
        condition = "negative"
    return (check.check_name, check.column, check.group_by, condition)


def make_run_checks_node(load_data: DataLoader) -> Callable[[InvestigationState], StateUpdate]:
    """Create a node that runs each new planned check once and records the results."""

    def run_checks(state: InvestigationState) -> StateUpdate:
        if state.analysis_plan is None:
            return {}

        already_run = {_result_key(result) for result in state.check_results if result.succeeded}
        pending = [
            check
            for check in state.analysis_plan.planned_checks()
            if _planned_key(check) not in already_run
        ]
        if not pending:
            return {}

        try:
            if state.request.data_uri is None:
                missing_uri = "the request has no data_uri"
                raise ValueError(missing_uri)  # noqa: TRY301
            df = load_data(state.request.data_uri)
        except Exception as error:
            message = f"Could not load batch data: {type(error).__name__}: {error}"
            failed = [
                CheckResult(
                    check_name=check.check_name,
                    params={},
                    metrics={},
                    succeeded=False,
                    error=message,
                )
                for check in pending
            ]
            return {"check_results": [*state.check_results, *failed]}

        new_results = [run_check(df, check) for check in pending]
        return {"check_results": [*state.check_results, *new_results]}

    return run_checks
