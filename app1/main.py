import re
import zipfile
from email import policy
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app1.ai.complaint_graph import ComplaintGraph
from app1.database import Base, SQLALCHEMY_DATABASE_URL, engine, get_db
from app1.models import Complaint
from app1.schemas import (
    ComplaintAnalysisRequest,
    ComplaintAssistantRequest,
    ComplaintCreate,
    ComplaintIntake,
    ComplaintResponse,
    ComplaintTextAnalysisRequest,
    ComplaintUpdate,
)

app = FastAPI(title="AIVOA Complaint Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

complaint_graph = ComplaintGraph()


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)



initialize_database()


@app.get("/")
def root():
    return {"message": "AIVOA backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/complaints", response_model=list[ComplaintResponse])
@app.get("/api/complaints", response_model=list[ComplaintResponse])
def get_complaints(db: Session = Depends(get_db)):
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()


@app.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
@app.get("/api/complaints/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@app.post("/complaints", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_legacy_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    analysis = complaint_graph.analyze(payload.description, payload.category)
    complaint_data = analysis["complaint"]

    complaint = Complaint(
        title=payload.title,
        description=payload.description,
        category=analysis["category"],
        complaint_type=complaint_data["complaint_type"],
        status="new",
        severity=analysis["severity"],
        initial_severity=analysis["severity"],
        priority=complaint_data["priority"],
        source=payload.source,
        complaint_source=payload.source,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@app.post("/api/complaints", status_code=status.HTTP_201_CREATED)
def create_intake_complaint(payload: ComplaintIntake, db: Session = Depends(get_db)):
    data = _intake_to_db_values(payload)
    complaint = Complaint(**data)

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {"message": "Complaint saved successfully", "complaint": _complaint_to_intake(complaint)}


@app.put("/complaints/{complaint_id}", response_model=ComplaintResponse)
@app.put("/api/complaints/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: int,
    payload: ComplaintUpdate,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(complaint, key, value)

    db.commit()
    db.refresh(complaint)
    return complaint


@app.delete("/complaints/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
@app.delete("/api/complaints/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    db.delete(complaint)
    db.commit()
    return None


@app.post("/complaints/analyze")
def analyze_complaint(payload: ComplaintAnalysisRequest):
    text = payload.text or payload.description or ""
    if not text.strip():
        raise HTTPException(status_code=422, detail="Complaint text is required")
    return complaint_graph.analyze(text, payload.category)


@app.post("/api/complaints/analyze-text")
def analyze_complaint_text(
    payload: ComplaintTextAnalysisRequest
):
    if not payload.text.strip():
        raise HTTPException(
            status_code=422,
            detail="Complaint text is required"
        )

    return complaint_graph.analyze(
        payload.text,
        source="Email / Text"
    )


@app.post("/api/complaints/assistant")
def complaint_assistant(payload: ComplaintAssistantRequest):
    try:
        return complaint_graph.assistant_update(payload.message, payload.complaint)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Assistant unavailable: {exc}") from exc


@app.post("/api/complaints/analyze-file")
async def analyze_complaint_file(
    request: Request
):
    filename, contents, content_type = (
        await read_multipart_file(request)
    )

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 10MB"
        )

    text = extract_text_from_upload(
        filename,
        contents,
        content_type
    )

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Unable to extract text from file"
        )

    return complaint_graph.analyze(
        text,
        source=f"File: {filename}"
    )


def _intake_to_db_values(payload: ComplaintIntake) -> dict:
    complaint_type = payload.complaintType or "General"
    severity = payload.initialSeverity or "Medium"
    title_parts = [payload.productName, complaint_type]
    title = " - ".join(part for part in title_parts if part).strip() or "Untitled complaint"

    return {
        "title": title,
        "description": payload.description or "",
        "complaint_source": payload.complaintSource,
        "customer_name": payload.customerName,
        "product_name": payload.productName,
        "product_strength": payload.productStrength,
        "batch_number": payload.batchNumber,
        "manufacturing_date": payload.manufacturingDate,
        "expiry_date": payload.expiryDate,
        "quantity_affected": payload.quantityAffected,
        "complaint_type": complaint_type,
        "complaint_date": payload.complaintDate,
        "initial_severity": severity,
        "priority": payload.priority or _priority_for_severity(severity),
        "category": complaint_type,
        "severity": severity,
        "source": payload.complaintSource or "web",
        "status": "new",
    }


def _complaint_to_intake(complaint: Complaint) -> dict:
    return {
        "id": complaint.id,
        "complaint_source": complaint.complaint_source,
        "customer_name": complaint.customer_name,
        "product_name": complaint.product_name,
        "product_strength": complaint.product_strength,
        "batch_number": complaint.batch_number,
        "manufacturing_date": complaint.manufacturing_date,
        "expiry_date": complaint.expiry_date,
        "quantity_affected": complaint.quantity_affected,
        "complaint_type": complaint.complaint_type,
        "complaint_date": complaint.complaint_date,
        "description": complaint.description,
        "initial_severity": complaint.initial_severity,
        "severity": complaint.severity,
        "priority": complaint.priority,
        "status": complaint.status,
    }


def _priority_for_severity(severity: str) -> str:
    return {
        "Critical": "Urgent",
        "High": "High",
        "Medium": "Normal",
        "Low": "Low",
    }.get(severity, "Normal")


def extract_text_from_upload(filename: str, contents: bytes, content_type: str) -> str:
    extension = Path(filename).suffix.lower()

    if extension in {".txt", ".log"} or content_type.startswith("text/"):
        return decode_bytes(contents)

    if extension == ".eml" or content_type == "message/rfc822":
        return extract_eml_text(contents)

    if extension == ".docx":
        return extract_docx_text(contents)

    if extension == ".pdf" or content_type == "application/pdf":
        return extract_pdf_text(contents)

    raise HTTPException(status_code=400, detail="Supported formats: PDF, DOCX, TXT and EML")


async def read_multipart_file(request: Request) -> tuple[str, bytes, str]:
    content_type = request.headers.get("content-type", "")
    boundary_match = re.search(r'boundary="?([^";]+)"?', content_type)
    if "multipart/form-data" not in content_type or not boundary_match:
        raise HTTPException(status_code=400, detail="Expected multipart/form-data upload")

    boundary = boundary_match.group(1).encode()
    body = await request.body()
    delimiter = b"--" + boundary

    for part in body.split(delimiter):
        part = part.strip()
        if not part or part == b"--":
            continue

        header_blob, separator, payload = part.partition(b"\r\n\r\n")
        if not separator:
            continue

        headers = decode_bytes(header_blob)
        if 'name="file"' not in headers:
            continue

        filename_match = re.search(r'filename="([^"]*)"', headers)
        type_match = re.search(r"(?im)^content-type:\s*(.+)$", headers)
        filename = filename_match.group(1) if filename_match else "complaint.txt"
        file_type = type_match.group(1).strip() if type_match else "application/octet-stream"

        return filename, payload.rstrip(b"\r\n-"), file_type

    raise HTTPException(status_code=400, detail="No file field found in upload")


def decode_bytes(contents: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    return contents.decode("utf-8", errors="ignore")


def extract_eml_text(contents: bytes) -> str:
    message = BytesParser(policy=policy.default).parsebytes(contents)
    parts = []

    if message.get("subject"):
        parts.append(f"Subject: {message.get('subject')}")
    if message.get("from"):
        parts.append(f"From: {message.get('from')}")

    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                parts.append(part.get_content())
    elif message.get_content_type() == "text/plain":
        parts.append(message.get_content())

    return "\n".join(parts)


def extract_docx_text(contents: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(contents)) as archive:
            xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=422, detail="Unable to read DOCX file") from exc

    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace))
        if text.strip():
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_pdf_text(contents: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(contents))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Unable to read PDF file") from exc

    text = "\n\n".join(page.strip() for page in pages if page.strip())
    if text:
        return text

    raise HTTPException(
        status_code=422,
        detail="PDF contains no selectable text. Upload a text-based PDF or paste its contents.",
    )


def _unescape_pdf_text(value: str) -> str:
    return (
        value.replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\\", "\\")
        .replace(r"\n", "\n")
        .replace(r"\r", "\r")
        .replace(r"\t", "\t")
    )
