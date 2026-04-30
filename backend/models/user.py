"""
Developer (user) database model.
Tracks per-developer statistics across all reviewed Pull Requests.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from backend.database import Base


class Developer(Base):
    """Represents a GitHub developer with aggregated review statistics."""

    __tablename__ = "developers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    github_username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="GitHub username (unique identifier)",
    )
    total_reviews: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of PRs reviewed for this developer",
    )
    avg_risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Running average risk score across all reviews",
    )
    total_critical_issues: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Lifetime count of critical issues found",
    )
    total_high_issues: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Lifetime count of high severity issues found",
    )
    total_medium_issues: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Lifetime count of medium severity issues found",
    )
    total_low_issues: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Lifetime count of low severity issues found",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Developer @{self.github_username} reviews={self.total_reviews} avg_risk={self.avg_risk_score:.1f}>"
