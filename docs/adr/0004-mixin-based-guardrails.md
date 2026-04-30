# Mixin-Based Guardrails Subpackage

The `design_quality/guardrails/` subpackage uses mixins (`ChecksMixin`, `ScoringMixin`, `ProbeMixin`, `AnalysisMixin`, `FixesMixin`) composed into a single `DesignQualityGuardrails` class. This keeps each module under 800 LOC while keeping the public interface (`analyze()`) in one place. Splitting by concern (checks, scoring, probing) is preferable to splitting by layer because guardrail behavior is tightly coupled within each concern.
