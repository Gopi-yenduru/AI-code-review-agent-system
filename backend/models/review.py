"""
Review and Issue database models.
Stores AI code review results for each Pull Request.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentType(str, enum.Enum):
    """Types of AI review agents."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"


class Severity(str, enum.Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewStatus(str, enum.Enum):
    """Review processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Review Model
# ---------------------------------------------------------------------------

class Review(Base):
    """Represents a single AI code review for a Pull Request."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    pr_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Full URL to the Pull Request on GitHub",
    )
    repo_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Repository in 'owner/repo' format",
    )
    pr_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Pull Request number",
    )
    pr_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Pull Request title",
    )
    author: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="GitHub username of PR author",
    )
    overall_risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="Calculated risk score 0-100",
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, name="review_status"),
        nullable=False,
        default=ReviewStatus.PENDING,
        doc="Processing status of the review",
    )
    quality_score: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=None,
        doc="Code quality score 0-100 from Quality agent",
    )
    quality_highlights: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="JSON string of positive quality highlights",
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

    # Relationships
    issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_reviews_created_at", "created_at"),
        Index("ix_reviews_author_created", "author", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Review {self.repo_name}#{self.pr_number} risk={self.overall_risk_score}>"


# ---------------------------------------------------------------------------
# Issue Model
# ---------------------------------------------------------------------------

class Issue(Base):
    """Represents a single issue found by an AI review agent."""

    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_type: Mapped[AgentType] = mapped_column(
        SAEnum(AgentType, name="agent_type"),
        nullable=False,
        doc="Which agent detected this issue",
    )
    severity: Mapped[Severity] = mapped_column(
        SAEnum(Severity, name="severity"),
        nullable=False,
        doc="Issue severity level",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed description of the issue",
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        doc="Line number in the diff where the issue was found",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        default=None,
        doc="File path where the issue was found",
    )
    suggestion: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default=None,
        doc="Suggested fix for the issue",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="issues",
    )

    # Indexes
    __table_args__ = (
        Index("ix_issues_agent_severity", "agent_type", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Issue [{self.agent_type.value}] {self.severity.value}: {self.description[:50]}>"
