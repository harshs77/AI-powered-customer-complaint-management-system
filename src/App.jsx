import { useRef, useState } from "react";

import {
  Bell,
  CalendarDays,
  Check,
  ChevronDown,
  CloudUpload,
  FileText,
  Info,
  Paperclip,
  RotateCcw,
  Save,
  Send,
  Sparkles,
  ShieldAlert,
  X,
} from "lucide-react";

import { useDispatch, useSelector } from "react-redux";

import {
  addChatMessage,
  analyzeComplaintFile,
  analyzeComplaintText,
  resetComplaint,
  saveComplaint,
  sendAssistantMessage,
  setPastedText,
  setSelectedFile,
  updateField,
} from "./features/complaintSlice";


function App() {
  const dispatch = useDispatch();

  const fileInputRef = useRef(null);

  const {
    form,
    extractionStatus,
    extractionProgress,
    selectedFile,
    pastedText,
    error,
    saving,
    saveSuccess,
    saveError,
    chatMessages,
    chatLoading,
    riskAssessment,
  } = useSelector(
    (state) => state.complaint
  );

  const [showPasteBox, setShowPasteBox] =
    useState(false);

  const [chatText, setChatText] =
    useState("");


  // ----------------------------------
  // INPUT HANDLERS
  // ----------------------------------

  const handleFieldChange = (
    field,
    value
  ) => {
    dispatch(
      updateField({
        field,
        value,
      })
    );
  };


  const validateFile = (file) => {
    const allowedTypes = [
      "application/pdf",
      "text/plain",
      "message/rfc822",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    const allowedExtensions = [
      ".pdf",
      ".docx",
      ".txt",
      ".eml",
    ];

    const extension =
      "." +
      file.name
        .split(".")
        .pop()
        .toLowerCase();

    const validType =
      allowedTypes.includes(
        file.type
      ) ||
      allowedExtensions.includes(
        extension
      );

    if (!validType) {
      alert(
        "Supported formats: PDF, DOCX, TXT and EML"
      );

      return false;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert(
        "Maximum file size is 10MB"
      );

      return false;
    }

    return true;
  };


  const handleFile = (file) => {
    if (!file) return;

    if (!validateFile(file)) return;

    dispatch(
      setSelectedFile({
        name: file.name,
        size: file.size,
      })
    );

    dispatch(
      analyzeComplaintFile(file)
    );
  };


  const handleFileChange = (event) => {
    const file =
      event.target.files?.[0];

    handleFile(file);
  };


  const handleBrowse = () => {
    fileInputRef.current?.click();
  };


  const handlePasteAnalyze = () => {
    if (!pastedText.trim()) {
      return;
    }

    dispatch(
      analyzeComplaintText(
        pastedText.trim()
      )
    );
  };


  // ----------------------------------
  // RESET
  // ----------------------------------

  const handleReset = () => {
    dispatch(resetComplaint());

    setShowPasteBox(false);
    setChatText("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };


  // ----------------------------------
  // SAVE
  // ----------------------------------

  const handleSave = () => {
    dispatch(saveComplaint());
  };


  // ----------------------------------
  // CHAT
  // ----------------------------------

  const handleChatSubmit = () => {
    const message = chatText.trim();

    if (!message || chatLoading) {
      return;
    }

    dispatch(
      addChatMessage({
        role: "user",
        content: message,
      })
    );

    setChatText("");
    dispatch(sendAssistantMessage(message));
  };


  const handleChatKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      handleChatSubmit();
    }
  };


  // ----------------------------------
  // UI
  // ----------------------------------

  return (
    <div className="app-shell">

      {/* HEADER */}
      <header className="top-header">

        <div className="brand-area">

          <div className="brand-mark">
            A
          </div>

          <div>
            <div className="brand-name">
              AIVOA
            </div>

            <div className="brand-subtitle">
              Quality Management System
            </div>
          </div>

        </div>

        <div className="header-right">

          <button className="icon-button">
            <Bell size={18} />
          </button>

          <div className="avatar">
            H
          </div>

        </div>

      </header>


      {/* MAIN */}
      <main className="main-container">

        {/* LEFT PANEL */}
        <section className="complaint-panel">

          <div className="panel-title-row">

            <div>
              <h1>
                Log Customer Complaint
              </h1>

              <p>
                API &amp; FDF Quality Assurance Module
              </p>
            </div>

            <div className="status-badge">
              Pending Triage
            </div>

          </div>


          <div className="section-divider" />


          {/* SECTION 1 */}
          <FormSection
            number="1"
            title="ORIGIN & CUSTOMER DETAILS"
          >

            <FormField
              label="Complaint Source"
              value={form.complaintSource}
              placeholder="Awaiting AI extraction..."
              onChange={(value) =>
                handleFieldChange(
                  "complaintSource",
                  value
                )
              }
            />

            <FormField
              label="Customer Name"
              value={form.customerName}
              placeholder="Awaiting AI extraction..."
              onChange={(value) =>
                handleFieldChange(
                  "customerName",
                  value
                )
              }
            />

          </FormSection>


          {/* SECTION 2 */}
          <FormSection
            number="2"
            title="PRODUCT & BATCH IDENTIFICATION"
          >

            <FormField
              label="Product Name"
              value={form.productName}
              placeholder="Awaiting AI extraction..."
              onChange={(value) =>
                handleFieldChange(
                  "productName",
                  value
                )
              }
            />

            <FormField
              label="Product Strength/Grade"
              value={form.productStrength}
              placeholder="Awaiting AI extraction..."
              onChange={(value) =>
                handleFieldChange(
                  "productStrength",
                  value
                )
              }
            />

            <FormField
              label="Batch/Lot Number"
              value={form.batchNumber}
              placeholder="Awaiting AI extraction..."
              onChange={(value) =>
                handleFieldChange(
                  "batchNumber",
                  value
                )
              }
            />

            <DateField
              label="Manufacturing Date"
              value={form.manufacturingDate}
              onChange={(value) =>
                handleFieldChange(
                  "manufacturingDate",
                  value
                )
              }
            />

            <DateField
              label="Expiry Date"
              value={form.expiryDate}
              onChange={(value) =>
                handleFieldChange(
                  "expiryDate",
                  value
                )
              }
            />

            <FormField
              label="Quantity Affected"
              value={form.quantityAffected}
              placeholder="Awaiting AI extraction..."
              suffix="kg"
              onChange={(value) =>
                handleFieldChange(
                  "quantityAffected",
                  value
                )
              }
            />

          </FormSection>


          {/* SECTION 3 */}
          <FormSection
            number="3"
            title="COMPLAINT DETAILS"
          >

            <FormField
              label="Complaint Type"
              value={form.complaintType}
              placeholder="Awaiting AI extraction..."
              onChange={(value) =>
                handleFieldChange(
                  "complaintType",
                  value
                )
              }
            />

            <DateField
              label="Complaint Date"
              value={form.complaintDate}
              onChange={(value) =>
                handleFieldChange(
                  "complaintDate",
                  value
                )
              }
            />

            <div className="field field-full">

              <label>
                Detailed Complaint Description
              </label>

              <textarea
                value={form.description}
                placeholder="Awaiting AI extraction..."
                onChange={(event) =>
                  handleFieldChange(
                    "description",
                    event.target.value
                  )
                }
              />

            </div>

          </FormSection>


          {/* SECTION 4 */}
          <FormSection
            number="4"
            title="INITIAL ASSESSMENT & PRIORITY"
          >

            <SelectField
              label="Initial Severity"
              value={form.initialSeverity}
              onChange={(value) =>
                handleFieldChange(
                  "initialSeverity",
                  value
                )
              }
              options={[
                "",
                "Low",
                "Medium",
                "High",
                "Critical",
              ]}
            />

            <SelectField
              label="Priority"
              value={form.priority}
              onChange={(value) =>
                handleFieldChange(
                  "priority",
                  value
                )
              }
              options={[
                "",
                "Low",
                "Normal",
                "High",
                "Urgent",
              ]}
            />

          </FormSection>


          {/* AI RISK COPILOT */}
          <section className="risk-copilot">
            <div className="risk-copilot-heading">
              <div className="risk-copilot-title">
                <ShieldAlert size={17} />
                AI COPILOT RISK ASSESSMENT
              </div>
              <span className="risk-copilot-badge">RECOMMENDATION</span>
            </div>

            {riskAssessment.level ? (
              <>
                <div className="risk-copilot-summary">
                  <div className={`risk-level risk-${riskAssessment.level.toLowerCase()}`}>
                    {riskAssessment.level} risk
                  </div>
                  <div className="risk-completeness">
                    {riskAssessment.completenessScore}% complete
                  </div>
                </div>
                <p className="risk-reason">{riskAssessment.reason || "No additional risk rationale provided."}</p>
                {riskAssessment.keyRisks.length > 0 && (
                  <ul className="risk-list">
                    {riskAssessment.keyRisks.map((risk, index) => (
                      <li key={`${risk}-${index}`}>{risk}</li>
                    ))}
                  </ul>
                )}
                <div className="risk-action">
                  <strong>Recommended action</strong>
                  <span>{riskAssessment.recommendedAction || "Review and triage complaint."}</span>
                </div>
                {riskAssessment.missingFields.length > 0 && (
                  <div className="risk-missing">
                    Missing details: {riskAssessment.missingFields.join(", ")}
                  </div>
                )}
              </>
            ) : (
              <p className="risk-empty">Analyze a complaint to generate an AI risk recommendation.</p>
            )}
          </section>


          {/* ERROR */}
          {(error || saveError) && (
            <div className="error-box">
              <X size={17} />
              {error || saveError}
            </div>
          )}


          {/* SUCCESS */}
          {saveSuccess && (
            <div className="success-box">
              <Check size={17} />
              Complaint saved successfully.
            </div>
          )}


          {/* FOOTER BUTTONS */}
          <div className="form-footer">

            <button
              className="reset-button"
              onClick={handleReset}
            >
              <RotateCcw size={16} />
              Reset Form
            </button>

            <button
              className="save-button"
              onClick={handleSave}
              disabled={saving}
            >
              <Save size={16} />

              {saving
                ? "Saving..."
                : "Save Complaint"}
            </button>

          </div>

        </section>


        {/* RIGHT PANEL */}
        <aside className="ai-panel">

          <div className="ai-title-row">

            <div className="ai-title">

              <div className="ai-icon">
                <Sparkles size={20} />
              </div>

              <div>
                <h2>
                  AI Complaint Intake Assistant
                </h2>
              </div>

            </div>

            <span className="beta-badge">
              BETA
            </span>

          </div>


          {/* FILE UPLOAD */}
          <div
            className="upload-box"
            onClick={handleBrowse}
          >

            <CloudUpload
              size={28}
              className="upload-icon"
            />

            <div className="upload-text">

              <strong>
                Drag &amp; drop complaint document here
              </strong>

              <span>
                or{" "}
                <b>
                  click to browse
                </b>
              </span>

            </div>

          </div>

          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept=".pdf,.docx,.txt,.eml"
            onChange={handleFileChange}
          />


          {selectedFile && (
            <div className="selected-file">

              <FileText size={17} />

              <span>
                {selectedFile.name}
              </span>

              <button
                onClick={(event) => {
                  event.stopPropagation();

                  dispatch(
                    setSelectedFile(null)
                  );
                }}
              >
                <X size={14} />
              </button>

            </div>
          )}


          {/* OR */}
          <div className="or-divider">

            <span />

            <b>OR</b>

            <span />

          </div>


          {/* PASTE TEXT */}
          <button
            className="paste-button"
            onClick={() =>
              setShowPasteBox(
                (previous) =>
                  !previous
              )
            }
          >

            <FileText size={18} />

            <span>
              Paste Complaint Text / Email
            </span>

          </button>


          {showPasteBox && (
            <div className="paste-area">

              <textarea
                value={pastedText}
                onChange={(event) =>
                  dispatch(
                    setPastedText(
                      event.target.value
                    )
                  )
                }
                placeholder="Paste complaint email or text here..."
              />

              <button
                className="analyze-text-button"
                onClick={handlePasteAnalyze}
              >
                Analyze Text
              </button>

            </div>
          )}


          {/* SUPPORTED FORMAT */}
          <div className="info-box">

            <Info size={16} />

            <div>

              <div>
                Supported formats:
                <strong>
                  {" "}
                  PDF, DOCX, TXT, EML
                </strong>
              </div>

              <div>
                Max file size:
                <strong>
                  {" "}
                  10MB
                </strong>
              </div>

            </div>

          </div>


          {/* EXTRACTION */}
          <div className="extraction-area">

            <div className="extraction-header">

              <span>
                EXTRACTION PROGRESS
              </span>

              <b>
                {extractionProgress}%
              </b>

            </div>

            <div className="progress-track">

              <div
                className="progress-fill"
                style={{
                  width:
                    `${extractionProgress}%`,
                }}
              />

            </div>


            <p className="progress-title">

              {extractionStatus ===
              "loading"
                ? "Analyzing document content and extracting key details..."
                : extractionStatus ===
                    "success"
                  ? "Extraction completed successfully."
                  : "Upload a complaint document to begin extraction."}

            </p>

            <p className="progress-subtitle">

              {extractionStatus ===
              "loading"
                ? "Please wait, this may take a few moments."
                : "AI will populate the complaint form automatically."}

            </p>

          </div>


          {/* ASSISTANT */}
          <div className="assistant-box">

            <div className="assistant-heading">
              AI ASSISTANT
            </div>


            {chatMessages.length ===
            0 ? (

              <div className="welcome-card">

                <div className="robot-icon">
                  <Sparkles size={19} />
                </div>

                <div>
                  Upload a complaint document
                  or paste text above.
                  <br />

                  I will automatically extract
                  the details and populate
                  the form for you.
                </div>

              </div>

            ) : (

              <div className="chat-history">

                {chatMessages.map(
                  (message, index) => (

                    <div
                      key={index}
                      className={
                        message.role ===
                        "user"
                          ? "chat-message user-message"
                          : "chat-message assistant-message"
                      }
                    >
                      {message.content}
                    </div>

                  )
                )}

              </div>

            )}


            {/* CHAT */}
            <div className="chat-input-area">

              <Paperclip
                size={17}
                className="attachment-icon"
              />

              <input
                value={chatText}
                onChange={(event) =>
                  setChatText(
                    event.target.value
                  )
                }
                onKeyDown={
                  handleChatKeyDown
                }
                placeholder="Ask me anything about this complaint..."
              />

              <button
                onClick={
                  handleChatSubmit
                }
                disabled={chatLoading}
              >
                <Send size={17} />
              </button>

            </div>

            <p className="ai-disclaimer">
              AI responses may contain errors.
              Please verify information.
            </p>

          </div>

        </aside>

      </main>

    </div>
  );
}


// =====================================================
// REUSABLE COMPONENTS
// =====================================================

function FormSection({
  number,
  title,
  children,
}) {
  return (
    <div className="form-section">

      <div className="section-heading">
        <span>
          {number}.
        </span>

        <h3>
          {title}
        </h3>
      </div>

      <div className="form-grid">
        {children}
      </div>

    </div>
  );
}


function FormField({
  label,
  value,
  placeholder,
  suffix,
  onChange,
}) {
  return (
    <div className="field">

      <label>
        {label}
      </label>

      <div className="input-wrapper">

        <input
          value={value}
          placeholder={placeholder}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
        />

        {suffix && (
          <span className="input-suffix">
            {suffix}
          </span>
        )}

      </div>

    </div>
  );
}


function DateField({
  label,
  value,
  onChange,
}) {
  return (
    <div className="field">

      <label>
        {label}
      </label>

      <div className="date-wrapper">

        <input
          type="text"
          value={value}
          placeholder="Awaiting AI extraction..."
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
        />

        <CalendarDays
          size={16}
        />

      </div>

    </div>
  );
}


function SelectField({
  label,
  value,
  options,
  onChange,
}) {
  return (
    <div className="field">

      <label>
        {label}
      </label>

      <div className="select-wrapper">

        <select
          value={value}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
        >

          <option value="">
            Awaiting AI extraction...
          </option>

          {options
            .filter(Boolean)
            .map((option) => (
              <option
                key={option}
                value={option}
              >
                {option}
              </option>
            ))}

        </select>

        <ChevronDown
          size={16}
        />

      </div>

    </div>
  );
}


export default App;
