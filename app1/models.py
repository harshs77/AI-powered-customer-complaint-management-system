from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app1.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, default="Untitled complaint")
    description = Column(Text, nullable=False, default="")

    complaint_source = Column(String(100), default="")
    customer_name = Column(String(255), default="")
    product_name = Column(String(255), default="")
    product_strength = Column(String(255), default="")
    batch_number = Column(String(255), default="")
    manufacturing_date = Column(String(50), default="")
    expiry_date = Column(String(50), default="")
    quantity_affected = Column(String(100), default="")
    complaint_type = Column(String(100), default="")
    complaint_date = Column(String(50), default="")
    initial_severity = Column(String(50), default="")
    priority = Column(String(50), default="")

    category = Column(String(100), default="general", index=True)
    status = Column(String(50), default="new", index=True)
    severity = Column(String(50), default="medium")
    source = Column(String(100), default="web")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
