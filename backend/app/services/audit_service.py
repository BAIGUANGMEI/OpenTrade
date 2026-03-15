from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:
    def log(self, db: Session, event_type: str, message: str, level: str = "info", details: dict | None = None) -> None:
        db.add(
            AuditLog(
                level=level,
                event_type=event_type,
                message=message,
                details_json=json.dumps(details or {}, default=str),
            )
        )


audit_service = AuditService()
