import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const initialForm = {
  complaintSource: "",
  customerName: "",
  productName: "",
  productStrength: "",
  batchNumber: "",
  manufacturingDate: "",
  expiryDate: "",
  quantityAffected: "",
  complaintType: "",
  complaintDate: "",
  description: "",
  initialSeverity: "",
  priority: "",
};

const initialState = {
  form: initialForm,

  extractionStatus: "idle",
  extractionProgress: 0,

  extracted: false,

  saving: false,
  saveSuccess: false,
  saveError: null,

  error: null,

  selectedFile: null,
  pastedText: "",

  chatMessages: [],
  chatLoading: false,

  riskAssessment: {
    level: "",
    reason: "",
    keyRisks: [],
    recommendedAction: "",
    completenessScore: 0,
    missingFields: [],
  },
};

export const analyzeComplaintFile = createAsyncThunk(
  "complaint/analyzeFile",
  async (file, { rejectWithValue }) => {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(
        `${API_URL}/api/complaints/analyze-file`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail ||
          error.message ||
          "Unable to analyze file"
      );
    }
  }
);

export const analyzeComplaintText = createAsyncThunk(
  "complaint/analyzeText",
  async (text, { rejectWithValue }) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/complaints/analyze-text`,
        {
          text,
        }
      );

      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail ||
          error.message ||
          "Unable to analyze complaint text"
      );
    }
  }
);

export const sendAssistantMessage = createAsyncThunk(
  "complaint/assistant",
  async (message, { getState, rejectWithValue }) => {
    try {
      const { complaint } = getState();
      const response = await axios.post(
        `${API_URL}/api/complaints/assistant`,
        { message, complaint: complaint.form }
      );
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail ||
          error.message ||
          "Unable to contact the AI assistant"
      );
    }
  }
);

export const saveComplaint = createAsyncThunk(
  "complaint/save",
  async (_, { getState, rejectWithValue }) => {
    try {
      const { complaint } = getState();

      const response = await axios.post(
        `${API_URL}/api/complaints`,
        complaint.form
      );

      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail ||
          error.message ||
          "Unable to save complaint"
      );
    }
  }
);

const complaintSlice = createSlice({
  name: "complaint",

  initialState,

  reducers: {
    updateField: (state, action) => {
      const { field, value } = action.payload;

      if (Object.prototype.hasOwnProperty.call(state.form, field)) {
        state.form[field] = value;
      }
    },

    setSelectedFile: (state, action) => {
      state.selectedFile = action.payload;
    },

    setPastedText: (state, action) => {
      state.pastedText = action.payload;
    },

    addChatMessage: (state, action) => {
      state.chatMessages.push(action.payload);
    },

    setChatLoading: (state, action) => {
      state.chatLoading = action.payload;
    },

    resetComplaint: () => {
      return initialState;
    },
  },

  extraReducers: (builder) => {
    builder

      // -----------------------------
      // FILE ANALYSIS
      // -----------------------------
      .addCase(
        analyzeComplaintFile.pending,
        (state) => {
          state.extractionStatus = "loading";
          state.extractionProgress = 10;
          state.error = null;
          state.extracted = false;
        }
      )

      .addCase(
        analyzeComplaintFile.fulfilled,
        (state, action) => {
          state.extractionStatus = "success";
          state.extractionProgress = 100;
          state.extracted = true;

          const data = action.payload;

          const complaint = data.complaint || data;

          state.form.complaintSource =
            complaint.complaint_source ||
            complaint.source ||
            state.form.complaintSource;

          state.form.customerName =
            complaint.customer_name || "";

          state.form.productName =
            complaint.product_name || "";

          state.form.productStrength =
            complaint.product_strength ||
            complaint.strength_grade ||
            "";

          state.form.batchNumber =
            complaint.batch_number ||
            complaint.batch_lot_number ||
            "";

          state.form.manufacturingDate =
            complaint.manufacturing_date || "";

          state.form.expiryDate =
            complaint.expiry_date || "";

          state.form.quantityAffected =
            complaint.quantity_affected || "";

          state.form.complaintType =
            complaint.complaint_type ||
            complaint.category ||
            "";

          state.form.complaintDate =
            complaint.complaint_date || "";

          state.form.description =
            complaint.description || "";

          state.form.initialSeverity =
            complaint.initial_severity ||
            complaint.severity ||
            "";

          state.form.priority =
            complaint.priority || "";

          state.riskAssessment = {
            level: data.risk?.risk_level || data.severity || complaint.severity || "",
            reason: data.risk?.risk_reason || "",
            keyRisks: data.risk?.key_risks || [],
            recommendedAction: data.risk?.recommended_action || data.recommended_action || "",
            completenessScore: data.completeness?.score || 0,
            missingFields: data.completeness?.missing_fields || [],
          };
        }
      )

      .addCase(
        analyzeComplaintFile.rejected,
        (state, action) => {
          state.extractionStatus = "error";
          state.extractionProgress = 0;
          state.error = action.payload;
        }
      )

      // -----------------------------
      // TEXT ANALYSIS
      // -----------------------------
      .addCase(
        analyzeComplaintText.pending,
        (state) => {
          state.extractionStatus = "loading";
          state.extractionProgress = 10;
          state.error = null;
          state.extracted = false;
        }
      )

      .addCase(
        analyzeComplaintText.fulfilled,
        (state, action) => {
          state.extractionStatus = "success";
          state.extractionProgress = 100;
          state.extracted = true;

          const data = action.payload;
          const complaint = data.complaint || data;

          state.form.complaintSource =
            complaint.complaint_source ||
            complaint.source ||
            "Email / Text";

          state.form.customerName =
            complaint.customer_name || "";

          state.form.productName =
            complaint.product_name || "";

          state.form.productStrength =
            complaint.product_strength ||
            complaint.strength_grade ||
            "";

          state.form.batchNumber =
            complaint.batch_number ||
            complaint.batch_lot_number ||
            "";

          state.form.manufacturingDate =
            complaint.manufacturing_date || "";

          state.form.expiryDate =
            complaint.expiry_date || "";

          state.form.quantityAffected =
            complaint.quantity_affected || "";

          state.form.complaintType =
            complaint.complaint_type ||
            complaint.category ||
            "";

          state.form.complaintDate =
            complaint.complaint_date || "";

          state.form.description =
            complaint.description || "";

          state.form.initialSeverity =
            complaint.initial_severity ||
            complaint.severity ||
            "";

          state.form.priority =
            complaint.priority || "";

          state.riskAssessment = {
            level: data.risk?.risk_level || data.severity || complaint.severity || "",
            reason: data.risk?.risk_reason || "",
            keyRisks: data.risk?.key_risks || [],
            recommendedAction: data.risk?.recommended_action || data.recommended_action || "",
            completenessScore: data.completeness?.score || 0,
            missingFields: data.completeness?.missing_fields || [],
          };
        }
      )

      .addCase(
        analyzeComplaintText.rejected,
        (state, action) => {
          state.extractionStatus = "error";
          state.extractionProgress = 0;
          state.error = action.payload;
        }
      )

      .addCase(sendAssistantMessage.pending, (state) => {
        state.chatLoading = true;
        state.error = null;
      })

      .addCase(sendAssistantMessage.fulfilled, (state, action) => {
        state.chatLoading = false;
        Object.entries(action.payload.updates || {}).forEach(
          ([field, value]) => {
            if (Object.prototype.hasOwnProperty.call(state.form, field)) {
              state.form[field] = value;
            }
          }
        );
        state.chatMessages.push({
          role: "assistant",
          content: action.payload.reply,
        });
      })

      .addCase(sendAssistantMessage.rejected, (state, action) => {
        state.chatLoading = false;
        state.error = action.payload;
        state.chatMessages.push({
          role: "assistant",
          content: action.payload || "The assistant could not process that request.",
        });
      })

      // -----------------------------
      // SAVE COMPLAINT
      // -----------------------------
      .addCase(
        saveComplaint.pending,
        (state) => {
          state.saving = true;
          state.saveSuccess = false;
          state.saveError = null;
        }
      )

      .addCase(
        saveComplaint.fulfilled,
        (state) => {
          state.saving = false;
          state.saveSuccess = true;
        }
      )

      .addCase(
        saveComplaint.rejected,
        (state, action) => {
          state.saving = false;
          state.saveError = action.payload;
        }
      );
  },
});

export const {
  updateField,
  setSelectedFile,
  setPastedText,
  addChatMessage,
  setChatLoading,
  resetComplaint,
} = complaintSlice.actions;

export default complaintSlice.reducer;