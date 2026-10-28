"""
KR -> Objective progress rollup.

Recomputed on WRITE (CheckIn creation / KR edits), never on read - progress
is a cached, stored value re-derived here and persisted.

Normalization rules per metric type (all clamped to [0, 100]):
  - boolean:     100 if current_value is "truthy" (non-zero), else 0.
  - number / percentage / currency:
        (current - start) / (target - start) * 100
    If target == start (degenerate range), treat as "done" (100) once
    current has reached/passed target, else 0.

Objective.progress_pct is a weight-aware average across:
  - every KeyResult directly on the objective (weight = kr.weight if set,
    else 1 - i.e. default equal weighting), and
  - every child Objective's own progress_pct (alignment rollup), each
    weighted 1 alongside the KRs.
An objective with neither KRs nor children has progress 0.

Rollups propagate upward: recalculating an objective also recalculates its
parent (if any), all the way to the root, so a 2+ level alignment chain
always reflects the latest leaf-level check-in.
"""
from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")


def _clamp(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 100:
        return Decimal("100")
    return value


def _as_decimal(value) -> Decimal:
    """Coerce a value that may arrive as int/float/str (e.g. an
    unsaved/unrefreshed model instance assigned plain Python literals) into
    a Decimal, so arithmetic never silently falls through to float
    division."""
    return value if isinstance(value, Decimal) else Decimal(str(value))


def normalize_key_result_progress(key_result) -> Decimal:
    """Compute (but do not save) the progress_pct for a KeyResult given its
    current start/target/current values."""
    if key_result.metric_type == key_result.MetricType.BOOLEAN:
        return Decimal("100") if key_result.current_value else Decimal("0")

    start = _as_decimal(key_result.start_value)
    target = _as_decimal(key_result.target_value)
    current = _as_decimal(key_result.current_value)

    if target == start:
        return Decimal("100") if current >= target else Decimal("0")

    raw = (current - start) / (target - start) * Decimal("100")
    return _clamp(raw).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def recalculate_key_result(key_result, *, save=True) -> Decimal:
    progress = normalize_key_result_progress(key_result)
    key_result.progress_pct = progress
    if save:
        key_result.save(update_fields=["progress_pct"])
    return progress


def compute_objective_progress(objective) -> Decimal:
    items = []
    for kr in objective.key_results.all():
        weight = kr.weight if kr.weight is not None else Decimal("1")
        items.append((kr.progress_pct or Decimal("0"), Decimal(weight)))
    for child in objective.child_objectives.all():
        items.append((child.progress_pct or Decimal("0"), Decimal("1")))

    if not items:
        return Decimal("0")

    total_weight = sum(w for _, w in items)
    if total_weight == 0:
        return Decimal("0")

    weighted_sum = sum(v * w for v, w in items)
    return _clamp((weighted_sum / total_weight)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def recalculate_objective(objective, *, save=True) -> Decimal:
    """Recompute objective.progress_pct and propagate upward to any parent
    objective (alignment rollup)."""
    progress = compute_objective_progress(objective)
    objective.progress_pct = progress
    if save:
        objective.save(update_fields=["progress_pct"])
    if objective.parent_objective_id:
        recalculate_objective(objective.parent_objective, save=save)
    return progress


def apply_check_in(check_in) -> None:
    """Called on CheckIn creation: advance the KeyResult's current_value to
    the new check-in's value, recompute the KR's progress, then recompute
    the objective (and bubble up through any parent alignment chain)."""
    key_result = check_in.key_result
    key_result.current_value = check_in.value
    key_result.save(update_fields=["current_value"])
    recalculate_key_result(key_result)
    recalculate_objective(key_result.objective)
