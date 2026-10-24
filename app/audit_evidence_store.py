"""SQLite persistence and retrieval for structured audit evidence."""

import sqlite3
from pathlib import Path
from typing import Any

from app.audit_evidence import (
    AuditEvidenceRecord,
    audit_evidence_from_json,
    build_evidence_summary,
    calculate_evidence_fingerprint,
    validate_audit_evidence,
)
from app.database import DATABASE_FILE


class AuditEvidenceStore:
    """Persist immutable audit evidence separately from legacy audit events."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DATABASE_FILE
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create the evidence table without altering existing audit tables."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_evidence_records (
                    audit_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    anomaly_score REAL NOT NULL,
                    source TEXT,
                    record_json TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_audit_evidence_agent_timestamp
                ON audit_evidence_records (agent_id, timestamp DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_audit_evidence_decision_timestamp
                ON audit_evidence_records (decision, timestamp DESC)
                """
            )

    def save(self, record: AuditEvidenceRecord) -> dict[str, Any]:
        """Save a record; identical repeated saves are idempotent."""
        validate_audit_evidence(record)
        record_json = record.to_json()
        fingerprint = calculate_evidence_fingerprint(record)

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT record_json, fingerprint
                FROM audit_evidence_records
                WHERE audit_id = ?
                """,
                (record.audit_id,),
            ).fetchone()

            if existing is not None:
                if (
                    existing["record_json"] == record_json
                    and existing["fingerprint"] == fingerprint
                ):
                    return {
                        "audit_id": record.audit_id,
                        "fingerprint": fingerprint,
                        "inserted": False,
                    }
                raise ValueError(
                    "Conflicting audit evidence already exists for this audit_id"
                )

            connection.execute(
                """
                INSERT INTO audit_evidence_records (
                    audit_id, event_id, timestamp, agent_id, decision,
                    risk_score, anomaly_score, source, record_json, fingerprint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.event_id,
                    record.timestamp.isoformat(),
                    record.agent_id,
                    record.decision,
                    record.risk_score,
                    record.anomaly_score,
                    record.source,
                    record_json,
                    fingerprint,
                ),
            )

        return {
            "audit_id": record.audit_id,
            "fingerprint": fingerprint,
            "inserted": True,
        }

    def get(self, audit_id: str) -> AuditEvidenceRecord | None:
        """Retrieve one evidence record by its audit ID."""
        if not isinstance(audit_id, str) or not audit_id.strip():
            raise ValueError("audit_id must be a non-empty string")

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_json
                FROM audit_evidence_records
                WHERE audit_id = ?
                """,
                (audit_id.strip(),),
            ).fetchone()

        if row is None:
            return None
        return audit_evidence_from_json(row["record_json"])

    def list_records(
        self,
        *,
        agent_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List evidence newest-first with optional filters and pagination."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer between 1 and 1000")
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a non-negative integer")

        clauses: list[str] = []
        parameters: list[Any] = []

        for field, value in (("agent_id", agent_id), ("decision", decision)):
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{field} must be a non-empty string")
                clauses.append(f"{field} = ?")
                parameters.append(value.strip())

        where_sql = " WHERE " + " AND ".join(clauses) if clauses else ""

        with self._connect() as connection:
            total = connection.execute(
                "SELECT COUNT(*) FROM audit_evidence_records" + where_sql,
                parameters,
            ).fetchone()[0]

            rows = connection.execute(
                """
                SELECT record_json, fingerprint
                FROM audit_evidence_records
                """
                + where_sql
                + """
                ORDER BY timestamp DESC, audit_id ASC
                LIMIT ? OFFSET ?
                """,
                [*parameters, limit, offset],
            ).fetchall()

        records = []
        for row in rows:
            record = audit_evidence_from_json(row["record_json"])
            item = build_evidence_summary(record)
            item["timestamp"] = record.timestamp.isoformat()
            item["reason"] = record.reason
            item["fingerprint"] = row["fingerprint"]
            records.append(item)

        return {
            "records": records,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def verify(self, audit_id: str) -> dict[str, Any] | None:
        """Compare stored record contents with the stored fingerprint."""
        if not isinstance(audit_id, str) or not audit_id.strip():
            raise ValueError("audit_id must be a non-empty string")

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT record_json, fingerprint
                FROM audit_evidence_records
                WHERE audit_id = ?
                """,
                (audit_id.strip(),),
            ).fetchone()

        if row is None:
            return None

        record = audit_evidence_from_json(row["record_json"])
        calculated = calculate_evidence_fingerprint(record)
        return {
            "audit_id": audit_id.strip(),
            "valid": calculated == row["fingerprint"],
            "stored_fingerprint": row["fingerprint"],
            "calculated_fingerprint": calculated,
        }


__all__ = ["AuditEvidenceStore"]
