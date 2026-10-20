"""
Day 46 - Basic Evaluation Metrics

Provides deterministic binary-classification metrics for
research experiments.

The implementation is intentionally small so that it can be
used to validate experimental results independently.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryMetrics:
    """Confusion-matrix counts and derived metrics."""

    true_positive: int
    true_negative: int
    false_positive: int
    false_negative: int

    @property
    def total(self) -> int:
        return (
            self.true_positive
            + self.true_negative
            + self.false_positive
            + self.false_negative
        )

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0

        return (
            self.true_positive + self.true_negative
        ) / self.total

    @property
    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive

        if denominator == 0:
            return 0.0

        return self.true_positive / denominator

    @property
    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative

        if denominator == 0:
            return 0.0

        return self.true_positive / denominator

    @property
    def f1(self) -> float:
        denominator = self.precision + self.recall

        if denominator == 0:
            return 0.0

        return (
            2 * self.precision * self.recall
        ) / denominator

    @property
    def false_positive_rate(self) -> float:
        denominator = self.false_positive + self.true_negative

        if denominator == 0:
            return 0.0

        return self.false_positive / denominator

    @property
    def false_negative_rate(self) -> float:
        denominator = self.false_negative + self.true_positive

        if denominator == 0:
            return 0.0

        return self.false_negative / denominator


def binary_metrics(
    y_true: list[int],
    y_pred: list[int],
) -> BinaryMetrics:
    """
    Calculate binary classification metrics.

    Labels must contain only 0 and 1.
    """

    if len(y_true) != len(y_pred):
        raise ValueError(
            "y_true and y_pred must have the same length"
        )

    if not y_true:
        raise ValueError(
            "y_true and y_pred must not be empty"
        )

    valid_values = {0, 1}

    if any(value not in valid_values for value in y_true):
        raise ValueError(
            "y_true must contain only 0 and 1"
        )

    if any(value not in valid_values for value in y_pred):
        raise ValueError(
            "y_pred must contain only 0 and 1"
        )

    true_positive = sum(
        actual == 1 and predicted == 1
        for actual, predicted in zip(y_true, y_pred)
    )

    true_negative = sum(
        actual == 0 and predicted == 0
        for actual, predicted in zip(y_true, y_pred)
    )

    false_positive = sum(
        actual == 0 and predicted == 1
        for actual, predicted in zip(y_true, y_pred)
    )

    false_negative = sum(
        actual == 1 and predicted == 0
        for actual, predicted in zip(y_true, y_pred)
    )

    return BinaryMetrics(
        true_positive=true_positive,
        true_negative=true_negative,
        false_positive=false_positive,
        false_negative=false_negative,
    )