from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComplaintBase(BaseModel):
    title: str = Field(default="Untitled complaint", min_length=1, max_length=255)
    description: str = ""
    category: str = "general"
    severity: str = "medium"
    source: str = "web"


class ComplaintCreate(ComplaintBase):
    pass


class ComplaintUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    status: str | None = None
    severity: str | None = None
    source: str | None = None

    complaint_source: str | None = None
    customer_name: str | None = None
    product_name: str | None = None
    product_strength: str | None = None
    batch_number: str | None = None
    manufacturing_date: str | None = None
    expiry_date: str | None = None
    quantity_affected: str | None = None
    complaint_type: str | None = None
    complaint_date: str | None = None
    initial_severity: str | None = None
    priority: str | None = None


class ComplaintResponse(ComplaintBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str = "new"
    created_at: datetime
    updated_at: datetime


class ComplaintIntake(BaseModel):
    complaintSource: str = ""
    customerName: str = ""
    productName: str = ""
    productStrength: str = ""
    batchNumber: str = ""
    manufacturingDate: str = ""
    expiryDate: str = ""
    quantityAffected: str = ""
    complaintType: str = ""
    complaintDate: str = ""
    description: str = ""
    initialSeverity: str = ""
    priority: str = ""


class ComplaintAnalysisRequest(BaseModel):
    description: str | None = None
    category: str = "general"
    text: str | None = None


class ComplaintTextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1)


class ComplaintAssistantRequest(BaseModel):
    message: str = Field(..., min_length=1)
    complaint: dict = Field(default_factory=dict)
