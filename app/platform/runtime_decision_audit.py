"""
Varynx Day 74 - Runtime Audit Export Validation.

Provides validation for runtime security audit exports.

This module does not calculate risk, create security decisions,
authorize actions, or execute enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RuntimeDecisionAuditRecord:
    """Audit record for a runtime security decision."""

    agent_id: str
    decision: str
    evidence: tuple[str, ...]
    recorded_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "decision": self.decision,
            "evidence": list(self.evidence),
            "recorded_at": self.recorded_at,
        }


class RuntimeDecisionAudit:
    """Stores, retrieves, queries, summarizes, and exports audit evidence."""

    def __init__(self) -> None:
        self._records: Dict[str, RuntimeDecisionAuditRecord] = {}

    def record(
        self,
        agent_id: str,
        decision: str,
        evidence: Optional[List[str]] = None,
    ) -> RuntimeDecisionAuditRecord:

        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")

        if not isinstance(decision, str) or not decision.strip():
            raise ValueError("decision must be a non-empty string")

        if evidence is None:
            evidence = []

        if not isinstance(evidence, list):
            raise ValueError("evidence must be a list")

        record = RuntimeDecisionAuditRecord(
            agent_id=agent_id.strip(),
            decision=decision.strip().upper(),
            evidence=tuple(evidence),
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )

        self._records[record.agent_id] = record

        return record

    def get(
        self,
        agent_id: str,
    ) -> Optional[RuntimeDecisionAuditRecord]:
        return self._records.get(agent_id)

    def get_evidence(
        self,
        agent_id: str,
    ) -> List[str]:
        record = self.get(agent_id)

        if record is None:
            return []

        return list(record.evidence)

    def query_by_decision(
        self,
        decision: str,
    ) -> List[RuntimeDecisionAuditRecord]:

        if not isinstance(decision, str) or not decision.strip():
            raise ValueError("decision must be a non-empty string")

        normalized = decision.strip().upper()

        return [
            record
            for record in self._records.values()
            if record.decision == normalized
        ]

    def summary(self) -> Dict[str, Any]:
        decision_counts: Dict[str, int] = {}

        for record in self._records.values():
            decision_counts[record.decision] = (
                decision_counts.get(record.decision, 0) + 1
            )

        return {
            "total_records": len(self._records),
            "agents": len(self._records),
            "decision_counts": decision_counts,
        }

    def export(
        self,
        decision: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Export all records or records matching a decision."""

        if decision is None:
            records = list(self._records.values())
        else:
            records = self.query_by_decision(decision)

        return [
            record.to_dict()
            for record in records
        ]

    def export_page(
        self,
        page: int = 1,
        page_size: int = 10,
        decision: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export one page of audit records."""

        if not isinstance(page, int) or page < 1:
            raise ValueError("page must be an integer greater than 0")

        if not isinstance(page_size, int) or page_size < 1:
            raise ValueError(
                "page_size must be an integer greater than 0"
            )

        records = self.export(decision)

        total_records = len(records)
        total_pages = (
            (total_records + page_size - 1) // page_size
            if total_records
            else 0
        )

        start = (page - 1) * page_size
        end = start + page_size

        return {
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1 and total_pages > 0,
            "records": records[start:end],
        }

    def export_metadata(
        self,
        decision: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return metadata describing the current export scope."""

        records = self.export(decision)

        decision_counts: Dict[str, int] = {}

        for record in records:
            current = record["decision"]
            decision_counts[current] = (
                decision_counts.get(current, 0) + 1
            )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(records),
            "decision_filter": (
                decision.strip().upper()
                if isinstance(decision, str)
                else None
            ),
            "decision_counts": decision_counts,
        }

    def validate_export(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Validate the structure of exported audit records.

        Returns a validation report instead of modifying the records.
        """

        if records is None:
            records = self.export()

        if not isinstance(records, list):
            raise ValueError("records must be a list")

        errors: List[str] = []

        required_fields = {
            "agent_id",
            "decision",
            "evidence",
            "recorded_at",
        }

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(
                    f"record {index} must be a dictionary"
                )
                continue

            missing = required_fields - set(record.keys())

            if missing:
                errors.append(
                    f"record {index} missing fields: "
                    f"{sorted(missing)}"
                )

            if "agent_id" in record:
                if (
                    not isinstance(record["agent_id"], str)
                    or not record["agent_id"].strip()
                ):
                    errors.append(
                        f"record {index} has invalid agent_id"
                    )

            if "decision" in record:
                if (
                    not isinstance(record["decision"], str)
                    or not record["decision"].strip()
                ):
                    errors.append(
                        f"record {index} has invalid decision"
                    )

            if "evidence" in record:
                if not isinstance(record["evidence"], list):
                    errors.append(
                        f"record {index} evidence must be a list"
                    )

            if "recorded_at" in record:
                if (
                    not isinstance(record["recorded_at"], str)
                    or not record["recorded_at"].strip()
                ):
                    errors.append(
                        f"record {index} has invalid recorded_at"
                    )

        return {
            "valid": not errors,
            "record_count": len(records),
            "errors": errors,
        }

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {
            agent_id: record.to_dict()
            for agent_id, record in self._records.items()
        }

    def clear(self) -> None:
        self._records.clear()