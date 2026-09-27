"""PostgreSQL 表模型,字段级定义以 design/data_schemas.md v1.1 §1 为唯一依据。

M1 范围: regulators / penalties / penalty_embeddings 三张表。
penalties 中引用未建表(entities/persons/legal_provisions, M2+)的外键列
本期只建列、不加 FK 约束,待对应表落地后由后续迁移补约束。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 枚举值与 data_schemas §1 保持同名
REGULATOR_SYSTEM = ("nfra", "pbc", "safe")
REGULATOR_LEVEL = ("head_office", "provincial", "branch")
SUBJECT_TYPE = ("institution", "individual")
PENALTY_TYPE = (
    "fine",
    "warning",
    "confiscation",
    "business_ban",
    "license_revoke",
    "practice_ban",
    "position_disqualify",
)
PENALTY_SOURCE = ("nfra", "pbc", "safe", "legacy_cbirc", "import")


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Regulator(Base):
    """处罚机关表(data_schemas §1.3)。"""

    __tablename__ = "regulators"

    code: Mapped[str] = mapped_column(String, unique=True)  # 如 nfra / nfra_ln
    name: Mapped[str] = mapped_column(String)
    system: Mapped[str] = mapped_column(Enum(*REGULATOR_SYSTEM, name="regulator_system"))
    level: Mapped[str] = mapped_column(Enum(*REGULATOR_LEVEL, name="regulator_level"))
    parent_code: Mapped[str | None] = mapped_column(
        String, ForeignKey("regulators.code"), nullable=True
    )


class Penalty(Base):
    """罚单主表(data_schemas §1.2)。金额一律"分";原文字段永不覆盖。"""

    __tablename__ = "penalties"
    __table_args__ = (
        Index("ix_penalties_entity_decision", "entity_id", "decision_date"),
        Index("ix_penalties_person", "person_id"),
        Index("ix_penalties_regulator_publish", "regulator_code", "publish_date"),
        Index("ix_penalties_decision_date", "decision_date"),
    )

    doc_no: Mapped[str] = mapped_column(String, unique=True)
    doc_no_synthetic: Mapped[bool] = mapped_column(default=False)
    case_group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    regulator_code: Mapped[str] = mapped_column(String, ForeignKey("regulators.code"))
    regulator_name: Mapped[str] = mapped_column(String)
    regulator_level: Mapped[str] = mapped_column(Enum(*REGULATOR_LEVEL, name="regulator_level"))
    subject_type: Mapped[str] = mapped_column(Enum(*SUBJECT_TYPE, name="subject_type"))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # FK→entities(M2 建表后补约束)
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # FK→persons(M2 建表后补约束)
    entity_name_raw: Mapped[str] = mapped_column(String)
    person_role: Mapped[str | None] = mapped_column(String, nullable=True)
    violation_text: Mapped[str] = mapped_column(Text)
    legal_basis_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    legal_basis_ids: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # FK→legal_provisions(M2 建表后补约束)
    penalty_types: Mapped[list[str]] = mapped_column(
        ARRAY(Enum(*PENALTY_TYPE, name="penalty_type"))
    )
    fine_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # 分
    confiscation_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # 分
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    publish_date: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(Enum(*PENALTY_SOURCE, name="penalty_source"))
    source_url: Mapped[str] = mapped_column(String)
    raw_snapshot_path: Mapped[str] = mapped_column(String)
    parse_confidence: Mapped[float] = mapped_column(Float)
    parse_version: Mapped[str] = mapped_column(String)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)


class PenaltyEmbedding(Base):
    """案由向量(data_schemas §1.4),bge 系 1024 维;M1 只建表,向量化 M2 启用。"""

    __tablename__ = "penalty_embeddings"

    penalty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("penalties.id"), index=True
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
    model_version: Mapped[str] = mapped_column(String)
