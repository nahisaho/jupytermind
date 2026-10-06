"""Differential expression heuristic module (DES-AGENOM-060 / REQ-AGENOM-060)."""

from __future__ import annotations

from numbers import Integral

import numpy
from scipy import stats

from ai_genomics_scientist.validation import fail, ok, register_validator

_MODULE_NAME = "differential-expression"


def _is_non_negative_integer(value: object) -> bool:
    return isinstance(value, Integral) and not isinstance(value, bool) and value >= 0


def _differential_expression_validator(params: dict) -> dict:
    """DES-AGENOM-002 registered atomic validator for this module."""
    counts = params.get("counts")
    sample_groups = params.get("sample_groups")

    if not isinstance(counts, dict) or not counts:
        return fail("counts", "must be a non-empty dict of gene IDs to count lists")
    if not isinstance(sample_groups, list) or not sample_groups:
        return fail("sample_groups", "must be a non-empty list of group labels")
    if not all(isinstance(gene, str) for gene in counts):
        return fail("counts", "must have gene-ID strings as keys")
    if not all(isinstance(label, str) for label in sample_groups):
        return fail("sample_groups", "must contain only string group labels")

    distinct_labels = sorted(set(sample_groups))
    if len(distinct_labels) != 2:
        return fail("sample_groups", "must contain exactly 2 distinct group labels")
    if any(sample_groups.count(label) < 2 for label in distinct_labels):
        return fail(
            "sample_groups",
            "each of the exactly 2 groups must have at least 2 replicate samples",
        )

    num_samples = len(sample_groups)
    for values in counts.values():
        if not isinstance(values, list) or len(values) != num_samples:
            return fail("counts", "each gene's count list length must equal len(sample_groups)")

    invalid_genes = [
        gene
        for gene, values in counts.items()
        if not all(_is_non_negative_integer(value) for value in values)
    ]
    if invalid_genes:
        listed = ", ".join(f'"{gene}"' for gene in invalid_genes)
        return fail(
            "counts", f"must contain only non-negative integers (invalid gene(s): {listed})"
        )

    has_reference_gene = any(all(value > 0 for value in values) for values in counts.values())
    if not has_reference_gene:
        return fail(
            "counts",
            "must contain at least one gene with positive counts in every sample to compute size factors",
        )

    return ok()


register_validator(_MODULE_NAME, _differential_expression_validator)


def _median_of_ratios_size_factors(
    gene_ids: list[str], counts: dict, num_samples: int
) -> numpy.ndarray:
    """Classic median-of-ratios size factors, excluding any gene with a zero count."""
    reference_rows = [
        counts[gene_id] for gene_id in gene_ids if all(value > 0 for value in counts[gene_id])
    ]
    reference_matrix = numpy.array(reference_rows, dtype=float)
    geometric_means = numpy.exp(numpy.mean(numpy.log(reference_matrix), axis=1))
    ratios = reference_matrix / geometric_means[:, None]
    return numpy.median(ratios, axis=0)


def _benjamini_hochberg(p_values: numpy.ndarray) -> numpy.ndarray:
    """Pure-numpy Benjamini-Hochberg step-up correction."""
    num_tests = len(p_values)
    order = numpy.argsort(p_values)
    ranked = p_values[order]
    raw = ranked * num_tests / (numpy.arange(num_tests) + 1)
    monotone = numpy.minimum.accumulate(raw[::-1])[::-1]
    adjusted = numpy.empty(num_tests)
    adjusted[order] = numpy.clip(monotone, 0.0, 1.0)
    return adjusted


# @id CODE-AGENOM-060
# @implements REQ-AGENOM-060
# @design DES-AGENOM-060
def run_differential_expression(counts: dict, sample_groups: list) -> list[dict]:
    """Compute median-of-ratios normalized differential expression results."""
    gene_ids = list(counts.keys())
    num_samples = len(sample_groups)
    size_factors = _median_of_ratios_size_factors(gene_ids, counts, num_samples)

    group1_label, group2_label = sorted(set(sample_groups))
    group1_idx = [i for i, label in enumerate(sample_groups) if label == group1_label]
    group2_idx = [i for i, label in enumerate(sample_groups) if label == group2_label]

    results = []
    p_values = []
    base_means = []
    log2_fold_changes = []
    for gene_id in gene_ids:
        raw = numpy.array(counts[gene_id], dtype=float)
        normalized = raw / size_factors
        base_mean = float(normalized.mean())
        mean_group1 = normalized[group1_idx].mean()
        mean_group2 = normalized[group2_idx].mean()
        log2_fold_change = float(numpy.log2((mean_group2 + 1) / (mean_group1 + 1)))

        log_normalized = numpy.log2(normalized + 1)
        log_group1 = log_normalized[group1_idx]
        log_group2 = log_normalized[group2_idx]
        if numpy.var(log_group1) == 0 and numpy.var(log_group2) == 0:
            p_value = 1.0
        else:
            _, p_value = stats.ttest_ind(log_group1, log_group2, equal_var=False)
            p_value = float(p_value)

        base_means.append(base_mean)
        log2_fold_changes.append(log2_fold_change)
        p_values.append(p_value)

    padj = _benjamini_hochberg(numpy.array(p_values))

    for index, gene_id in enumerate(gene_ids):
        results.append(
            {
                "gene_id": gene_id,
                "base_mean": base_means[index],
                "log2_fold_change": log2_fold_changes[index],
                "p_value": p_values[index],
                "padj": float(padj[index]),
            }
        )

    return sorted(results, key=lambda item: (item["padj"], item["gene_id"]))
