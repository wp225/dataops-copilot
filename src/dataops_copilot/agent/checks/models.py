"""Data Modeling for Investigation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

type CheckName = Literal["value_range", "breakdown_by", "duplicate_rows"]
type BreakdownCondition = Literal["negative", "non_positive", "null"]


class CheckResult(BaseModel):
    """Base model for investigation checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    check_name: str
    params: dict[str, str]
    metrics: dict[str, float]
    succeeded: bool
    error: str | None = None

    def describe(self) -> str:
        """Return a one-line, human-readable label for this check run."""
        params = ", ".join(f"{key}={value}" for key, value in sorted(self.params.items()))
        return f"{self.check_name}({params})"


class PlannedCheck(BaseModel):
    """A catalog check the planner wants to run, with its parameters.

    The model is flat (not a discriminated union) so it maps cleanly onto
    Claude structured outputs. Parameter requirements per check are enforced
    when the check runs, and a violation becomes a failed CheckResult rather
    than a parse error.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    check_name: CheckName = Field(description="Which catalog check to run.")
    column: str | None = Field(
        default=None,
        description="Column to inspect. Required for value_range and breakdown_by.",
    )
    group_by: str | None = Field(
        default=None,
        description="Column to group by. Required for breakdown_by.",
    )
    condition: BreakdownCondition | None = Field(
        default=None,
        description="Which rows breakdown_by counts. Defaults to 'negative'.",
    )
    reason: str = Field(description="Why this check helps test the hypothesis.")

    def key(self) -> tuple[str, str | None, str | None, str | None]:
        """Return the identity of this check, ignoring the free-text reason."""
        return (self.check_name, self.column, self.group_by, self.condition)
