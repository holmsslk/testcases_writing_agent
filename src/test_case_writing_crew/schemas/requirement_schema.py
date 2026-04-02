"""Requirement-related schemas for testcase generation MVP."""

from dataclasses import dataclass, field

from .validators import ensure_bool, ensure_in_set, ensure_non_empty_str, ensure_str_list

CLARIFICATION_CATEGORIES = {
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

IMPACT_LEVELS = {"low", "medium", "high", "critical"}


@dataclass
class RequirementSummary:
    """Structured summary extracted from PRD/API/requirement-table inputs."""

    product_name: str = field(
        default="unknown_product",
        metadata={"description": "Product or system name."},
    )
    version: str = field(
        default="0.1.0",
        metadata={"description": "Target product version."},
    )
    scope: list[str] = field(
        default_factory=list,
        metadata={"description": "In-scope features and business areas."},
    )
    out_of_scope: list[str] = field(
        default_factory=list,
        metadata={"description": "Explicitly excluded features and areas."},
    )
    modules: list[str] = field(
        default_factory=list,
        metadata={"description": "Product modules involved in this release."},
    )
    user_roles: list[str] = field(
        default_factory=list,
        metadata={"description": "Roles interacting with the system."},
    )
    business_rules: list[str] = field(
        default_factory=list,
        metadata={"description": "Domain/business rules that constrain behavior."},
    )
    external_dependencies: list[str] = field(
        default_factory=list,
        metadata={"description": "External systems, devices, services, or APIs."},
    )
    non_functional_requirements: list[str] = field(
        default_factory=list,
        metadata={"description": "NFRs such as performance, security, and stability."},
    )
    risks: list[str] = field(
        default_factory=list,
        metadata={"description": "Known implementation, operation, or release risks."},
    )
    assumptions: list[str] = field(
        default_factory=list,
        metadata={"description": "Assumptions made for design and validation."},
    )

    def __post_init__(self) -> None:
        self.product_name = ensure_non_empty_str(self.product_name, "product_name")
        self.version = ensure_non_empty_str(self.version, "version")
        self.scope = ensure_str_list(self.scope, "scope")
        self.out_of_scope = ensure_str_list(self.out_of_scope, "out_of_scope")
        self.modules = ensure_str_list(self.modules, "modules")
        self.user_roles = ensure_str_list(self.user_roles, "user_roles")
        self.business_rules = ensure_str_list(self.business_rules, "business_rules")
        self.external_dependencies = ensure_str_list(
            self.external_dependencies,
            "external_dependencies",
        )
        self.non_functional_requirements = ensure_str_list(
            self.non_functional_requirements,
            "non_functional_requirements",
        )
        self.risks = ensure_str_list(self.risks, "risks")
        self.assumptions = ensure_str_list(self.assumptions, "assumptions")


@dataclass
class ClarificationQuestion:
    """Question raised during requirement-gap analysis before testcase drafting."""

    id: str = field(
        default="CQ-001",
        metadata={"description": "Unique clarification question identifier."},
    )
    category: str = field(
        default="functional",
        metadata={"description": "Question category such as functional/api/security."},
    )
    question: str = field(
        default="TBD clarification question",
        metadata={"description": "Concrete question sent for requirement clarification."},
    )
    impact: str = field(
        default="medium",
        metadata={"description": "Expected impact if unanswered (low/medium/high/critical)."},
    )
    required: bool = field(
        default=True,
        metadata={"description": "Whether an answer is mandatory before proceeding."},
    )

    def __post_init__(self) -> None:
        self.id = ensure_non_empty_str(self.id, "id")
        self.category = ensure_in_set(
            self.category,
            "category",
            CLARIFICATION_CATEGORIES,
        )
        self.question = ensure_non_empty_str(self.question, "question")
        self.impact = ensure_in_set(self.impact, "impact", IMPACT_LEVELS)
        self.required = ensure_bool(self.required, "required")
