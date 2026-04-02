"""Entry/exit gate schemas for quality criteria management."""

from dataclasses import dataclass, field

from .validators import ensure_bool, ensure_dataclass_list, ensure_in_set, ensure_non_empty_str, ensure_str_list

CRITERION_TYPES = {"entry", "exit", "quality", "risk", "process", "other"}
CRITERION_CATEGORIES = {
    "functional",
    "api",
    "permission",
    "boundary",
    "exception",
    "compatibility",
    "performance",
    "security",
    "stability",
    "dfx",
    "other",
}


@dataclass
class GateCriterion:
    """Single measurable criterion used for entry/exit quality checks."""

    criterion_id: str = field(
        default="GC-001",
        metadata={"description": "Unique gate criterion identifier."},
    )
    criterion_type: str = field(
        default="quality",
        metadata={"description": "Criterion type such as entry/exit/quality."},
    )
    category: str = field(
        default="functional",
        metadata={"description": "Coverage category this criterion belongs to."},
    )
    description: str = field(
        default="No criterion description provided.",
        metadata={"description": "Detailed criterion definition."},
    )
    threshold: str = field(
        default="TBD",
        metadata={"description": "Threshold definition, e.g., '>=95%'."},
    )
    mandatory: bool = field(
        default=True,
        metadata={"description": "Whether criterion is mandatory for pass."},
    )
    remarks: str = field(
        default="",
        metadata={"description": "Additional notes for this criterion."},
    )

    def __post_init__(self) -> None:
        self.criterion_id = ensure_non_empty_str(self.criterion_id, "criterion_id")
        self.criterion_type = ensure_in_set(
            self.criterion_type,
            "criterion_type",
            CRITERION_TYPES,
        )
        self.category = ensure_in_set(self.category, "category", CRITERION_CATEGORIES)
        self.description = ensure_non_empty_str(self.description, "description")
        self.threshold = ensure_non_empty_str(self.threshold, "threshold")
        self.mandatory = ensure_bool(self.mandatory, "mandatory")
        if not isinstance(self.remarks, str):
            raise TypeError("remarks must be str")
        self.remarks = self.remarks.strip()


@dataclass
class EntryExitCriteriaSet:
    """Combined set of entry and exit criteria for a project/release."""

    entry_criteria: list[GateCriterion] = field(
        default_factory=list,
        metadata={"description": "Criteria required before testcase generation/execution."},
    )
    exit_criteria: list[GateCriterion] = field(
        default_factory=list,
        metadata={"description": "Criteria required before release sign-off."},
    )
    project_specific_notes: list[str] = field(
        default_factory=list,
        metadata={"description": "Project-specific notes that impact gate decisions."},
    )

    def __post_init__(self) -> None:
        self.entry_criteria = ensure_dataclass_list(
            self.entry_criteria,
            "entry_criteria",
            GateCriterion,
        )
        self.exit_criteria = ensure_dataclass_list(
            self.exit_criteria,
            "exit_criteria",
            GateCriterion,
        )
        self.project_specific_notes = ensure_str_list(
            self.project_specific_notes,
            "project_specific_notes",
        )
