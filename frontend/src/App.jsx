import { useState, useEffect, useCallback } from "react";
import { api } from "./api/client";
import "./App.css";

const navigation = [
  { name: "Dashboard", icon: "grid" },
  { name: "Evidence", icon: "folder" },
  { name: "Integrity Verification", icon: "shield" },
  { name: "Sanitization", icon: "trash" },
  { name: "Cloud Verification", icon: "cloud" },
  { name: "Chain of Custody", icon: "link" },
  { name: "Reports", icon: "file" },
];

function Icon({ name, size = 20 }) {
  const paths = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    folder: (
      <path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    trash: (
      <>
        <path d="M3 6h18M8 6V4h8v2m3 0-1 14H6L5 6" />
        <path d="M10 11v5m4-5v5" />
      </>
    ),
    cloud: (
      <path d="M20 17.5a4.5 4.5 0 0 0-1.2-8.8A6.5 6.5 0 0 0 6 10a4 4 0 0 0 0 8h13" />
    ),
    link: (
      <>
        <path d="M10 13a5 5 0 0 0 7.1 0l3-3a5 5 0 0 0-7.1-7.1l-1.7 1.7" />
        <path d="M14 11a5 5 0 0 0-7.1 0l-3 3A5 5 0 0 0 11 21.1l1.7-1.7" />
      </>
    ),
    file: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6M8 13h8M8 17h8" />
      </>
    ),
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    bell: (
      <>
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M10 21h4" />
      </>
    ),
    settings: (
      <>
        <path d="M12 2v2m0 16v2m10-10h-2M4 12H2m17.07-7.07-1.41 1.41M6.34 17.66l-1.41 1.41m14.14 0-1.41-1.41M6.34 6.34 4.93 4.93" />
        <circle cx="12" cy="12" r="3" />
      </>
    ),
    arrow: <path d="M7 17 17 7M7 7h10v10" />,
    activity: <path d="M3 12h4l3-8 4 16 3-8h4" />,
    plus: <path d="M12 5v14M5 12h14" />,
    check: <path d="m5 12 4 4L19 6" />,
    refresh: (
      <>
        <path d="M20 7v5h-5" />
        <path d="M4 17v-5h5" />
        <path d="M5.5 9a7 7 0 0 1 12-2L20 12" />
        <path d="M4 12l2.5 5a7 7 0 0 0 12-2" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V4" />
        <path d="m7 9 5-5 5 5" />
        <path d="M4 20h16" />
      </>
    ),
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.grid}
    </svg>
  );
}

function getArray(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.events)) return data.events;
  if (Array.isArray(data?.logs)) return data.logs;
  if (Array.isArray(data?.records)) return data.records;
  if (Array.isArray(data?.evidence)) return data.evidence;
  return [];
}

function getChainStatus(data) {
  if (!data) return "—";

  const verified =
    data.verified ??
    data.valid ??
    data.chain_valid ??
    data.is_valid;

  if (verified === true) return "Verified";
  if (verified === false) return "Failed";

  const status = String(data.status || "").toLowerCase();

  if (status === "verified" || status === "valid") {
    return "Verified";
  }

  if (status === "failed" || status === "invalid") {
    return "Failed";
  }

  return "Available";
}

function getActivityText(item) {
  return (
    item.action ||
    item.event ||
    item.event_type ||
    item.operation ||
    item.description ||
    item.message ||
    item.type ||
    "Audit event recorded"
  );
}

function getActivityDate(item) {
  const value =
    item.timestamp ||
    item.created_at ||
    item.datetime ||
    item.time ||
    item.date;

  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

function formatBytes(bytes) {
  const value = Number(bytes);

  if (!Number.isFinite(value) || value < 0) return "—";
  if (value === 0) return "0 Bytes";

  const units = ["Bytes", "KB", "MB", "GB", "TB"];

  const index = Math.min(
    Math.floor(Math.log(value) / Math.log(1024)),
    units.length - 1
  );

  return `${(value / Math.pow(1024, index)).toFixed(
    index === 0 ? 0 : 2
  )} ${units[index]}`;
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}
/* ==========================================
   VANISH — INTRODUCTION PAGE
========================================== */

function IntroPage({ onLaunch }) {
  return (
    <div className="vanish-intro">

      <div className="intro-background-grid"></div>

      <div className="intro-content">

        <div className="intro-brand">
          <span className="intro-brand-mark">V</span>
          <span>VANISH</span>
        </div>

        <div className="intro-badge">
          DIGITAL FORENSIC AUDIT FRAMEWORK
        </div>

        <h1 className="intro-title">
          VANISH
        </h1>

        <div className="intro-subtitle">
          Beyond the Delete Button
        </div>

        <h2 className="intro-project-title">
          Evidence-Based Forensic Audit Framework
          for Verifying Digital Data Erasure
          Across Multi-Device and Cloud Environments
        </h2>

        <p className="intro-description">
          VANISH is a digital forensic audit prototype designed
          to assess digital evidence integrity, examine data
          sanitization outcomes, verify cloud-related erasure
          conditions, and maintain traceable evidence handling
          records.
        </p>

        <div className="intro-feature-grid">

          <div className="intro-feature">
            <div className="intro-feature-number">01</div>
            <h3>Evidence Integrity</h3>
            <p>
              Cryptographic hashing and verification
              to identify changes in digital evidence.
            </p>
          </div>

          <div className="intro-feature">
            <div className="intro-feature-number">02</div>
            <h3>Sanitization Verification</h3>
            <p>
              Examine sanitization outcomes using
              controlled verification procedures.
            </p>
          </div>

          <div className="intro-feature">
            <div className="intro-feature-number">03</div>
            <h3>Cloud Verification</h3>
            <p>
              Assess cloud-related deletion conditions
              through verification checks.
            </p>
          </div>

          <div className="intro-feature">
            <div className="intro-feature-number">04</div>
            <h3>Chain of Custody</h3>
            <p>
              Maintain traceable records of evidence
              handling and audit events.
            </p>
          </div>

        </div>

        <button
          className="intro-launch-button"
          onClick={onLaunch}
        >
          Launch VANISH
          <span> → </span>
        </button>

        <div className="intro-footer">
          <span>FORENSIC AUDIT SYSTEM</span>
          <span>PROTOTYPE v1.0</span>
        </div>

      </div>

    </div>
  );
}

function App() {
  const [showIntro, setShowIntro] = useState(true);
  
  const [activePage, setActivePage] = useState("Dashboard");

  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [backendError, setBackendError] = useState("");

  const [evidenceCount, setEvidenceCount] = useState("—");
  const [auditLogCount, setAuditLogCount] = useState("—");
  const [custodyCount, setCustodyCount] = useState("—");
  const [chainStatus, setChainStatus] = useState("Checking...");

  const [recentActivity, setRecentActivity] = useState([]);
  // Chain of Custody page state
const [custodyEventsList, setCustodyEventsList] = useState([]);
const [custodyLoading, setCustodyLoading] = useState(false);
const [custodyError, setCustodyError] = useState("");
const [custodyVerification, setCustodyVerification] = useState(null);
const [custodyAuditFilter, setCustodyAuditFilter] = useState("");

  // Evidence page state
  const [evidenceRecords, setEvidenceRecords] = useState([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState("");
  const [evidenceSearch, setEvidenceSearch] = useState("");
  const [scanLoading, setScanLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [evidenceMessage, setEvidenceMessage] = useState("");
  const [evidenceMessageType, setEvidenceMessageType] =
    useState("success");

  // Integrity verification state
  const [selectedAuditId, setSelectedAuditId] = useState("");
  const [integrityLoading, setIntegrityLoading] = useState(false);
  const [integrityError, setIntegrityError] = useState("");
  const [integrityResult, setIntegrityResult] = useState(null);

  // Sanitization verification state
  const [sanitizationTarget, setSanitizationTarget] = useState("");
  const [sanitizationMethod, setSanitizationMethod] =
    useState("unknown");
  const [storageType, setStorageType] = useState("filesystem");
  const [residualMarker, setResidualMarker] = useState("");
  const [sanitizationLoading, setSanitizationLoading] = useState(false);
  const [sanitizationError, setSanitizationError] = useState("");
  const [sanitizationResult, setSanitizationResult] = useState(null);

  // Cloud verification state
  const [cloudDeletionConfirmed, setCloudDeletionConfirmed] =
    useState(false);
  const [cloudResidualObjects, setCloudResidualObjects] =
    useState("");
  const [cloudRetainedVersions, setCloudRetainedVersions] =
    useState("");
  const [cloudBackupCopies, setCloudBackupCopies] =
    useState("");
  const [cloudRetentionActive, setCloudRetentionActive] =
    useState(false);
  const [cloudLocationsChecked, setCloudLocationsChecked] =
    useState("primary_storage");
  const [cloudEvidenceComplete, setCloudEvidenceComplete] =
    useState(true);
  const [cloudLoading, setCloudLoading] = useState(false);
  const [cloudError, setCloudError] = useState("");
  const [cloudResult, setCloudResult] = useState(null);
  // Reports page state
const [reportAuditId, setReportAuditId] = useState("");
const [reportLoading, setReportLoading] = useState(false);
const [reportError, setReportError] = useState("");
const [reportResult, setReportResult] = useState(null);

  const loadEvidence = useCallback(async () => {
    setEvidenceLoading(true);
    setEvidenceError("");

    try {
      const data = await api.evidence();
      const records = getArray(data);

      setEvidenceRecords(records);

      if (typeof data?.total === "number") {
        setEvidenceCount(data.total);
      } else {
        setEvidenceCount(records.length);
      }

      if (!selectedAuditId && records.length > 0) {
        const firstAuditId =
          records.find((record) => record.audit_id)?.audit_id || "";

        setSelectedAuditId(firstAuditId);
      }
    } catch (error) {
      setEvidenceError(error.message || "Failed to load evidence.");
    } finally {
      setEvidenceLoading(false);
    }
  }, [selectedAuditId]);

  const refreshDashboard = useCallback(async () => {
    try {
      const data = await api.evidence();
      const records = getArray(data);

      setEvidenceCount(
        typeof data?.total === "number"
          ? data.total
          : records.length
      );
    } catch {
      setEvidenceCount("Error");
    }
  }, []);

  useEffect(() => {
    api.health()
      .then((data) => {
        setBackendStatus(
          data.status === "healthy" ? "Connected" : "Unhealthy"
        );
      })
      .catch((error) => {
        setBackendStatus("Disconnected");
        setBackendError(error.message);
      });

    api.evidence()
      .then((data) => {
        const records = getArray(data);

        setEvidenceCount(
          typeof data?.total === "number"
            ? data.total
            : records.length
        );
      })
      .catch(() => {
        setEvidenceCount("Error");
      });

    api.auditLogs()
      .then((data) => {
        const logs = getArray(data);

        setAuditLogCount(
          typeof data?.total === "number"
            ? data.total
            : logs.length
        );

        setRecentActivity(logs.slice(0, 5));
      })
      .catch(() => {
        setAuditLogCount("Error");
      });

    api.custodyEvents()
      .then((data) => {
        const events = getArray(data);

        setCustodyCount(
          typeof data?.total === "number"
            ? data.total
            : events.length
        );
      })
      .catch(() => {
        setCustodyCount("Error");
      });

    api.verifyCustodyChain()
      .then((data) => {
        setChainStatus(getChainStatus(data));
      })
      .catch(() => {
        setChainStatus("Error");
      });
  }, []);
// Generate forensic report
const generateReport = useCallback(async () => {
  if (!reportAuditId.trim()) {
    setReportError("Please enter an Audit ID.");
    setReportResult(null);
    return;
  }

  setReportLoading(true);
  setReportError("");
  setReportResult(null);

  try {
    const data = await api.auditReport(reportAuditId.trim());
    setReportResult(data);
  } catch (error) {
    setReportError(error.message || "Failed to generate report.");
  } finally {
    setReportLoading(false);
  }
}, [reportAuditId]);

  // Load evidence records when relevant pages open
  useEffect(() => {
    if (
      activePage === "Evidence" ||
      activePage === "Integrity Verification" ||
      activePage === "Sanitization"
    ) {
      loadEvidence();
    }
  }, [activePage, loadEvidence]);

  async function handleScan() {
    setScanLoading(true);
    setEvidenceError("");
    setEvidenceMessage("");

    try {
      const result = await api.scanEvidence();

      setEvidenceMessage(
        `Scan completed successfully. ${
          result.records_saved ?? result.files_scanned ?? 0
        } evidence records processed.`
      );

      setEvidenceMessageType("success");

      await loadEvidence();
      await refreshDashboard();
    } catch (error) {
      setEvidenceError(error.message || "Evidence scan failed.");
    } finally {
      setScanLoading(false);
    }
  }

  async function handleUpload() {
    if (!selectedFile) {
      setEvidenceError("Please select a file before uploading.");
      return;
    }

    setUploadLoading(true);
    setEvidenceError("");
    setEvidenceMessage("");

    try {
      const result = await api.uploadEvidence(selectedFile);

      setEvidenceMessage(
        `Upload successful: ${result.file_name || selectedFile.name}`
      );

      setEvidenceMessageType("success");
      setSelectedFile(null);

      const fileInput = document.getElementById(
        "evidence-file-input"
      );

      if (fileInput) fileInput.value = "";

      await loadEvidence();
      await refreshDashboard();
    } catch (error) {
      setEvidenceError(error.message || "File upload failed.");
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleIntegrityVerification() {
    if (!selectedAuditId) {
      setIntegrityError("Please select an evidence Audit ID.");
      setIntegrityResult(null);
      return;
    }

    setIntegrityLoading(true);
    setIntegrityError("");
    setIntegrityResult(null);

    try {
      const result = await api.verifyAudit(selectedAuditId);
      setIntegrityResult(result);
    } catch (error) {
      setIntegrityError(
        error.message || "Integrity verification failed."
      );
    } finally {
      setIntegrityLoading(false);
    }
  }

  async function handleSanitizationVerification() {
    if (!sanitizationTarget.trim()) {
      setSanitizationError("Please select or enter a target file.");
      setSanitizationResult(null);
      return;
    }

    setSanitizationLoading(true);
    setSanitizationError("");
    setSanitizationResult(null);

    try {
      const result = await api.verifySanitization({
        target_path: sanitizationTarget.trim(),
        sanitization_method: sanitizationMethod,
        storage_type: storageType,
        residual_marker: residualMarker,
      });

      setSanitizationResult(result);
    } catch (error) {
      setSanitizationError(
        error.message || "Sanitization verification failed."
      );
    } finally {
      setSanitizationLoading(false);
    }
  }

  async function handleCloudVerification() {
    setCloudLoading(true);
    setCloudError("");
    setCloudResult(null);

    const parseList = (value) =>
      String(value || "")
        .split(/[\n,]+/)
        .map((item) => item.trim())
        .filter(Boolean);

    const payload = {
      deletion_confirmed: Boolean(cloudDeletionConfirmed),
      residual_objects: parseList(cloudResidualObjects),
      retained_versions: parseList(cloudRetainedVersions),
      backup_copies: parseList(cloudBackupCopies),
      retention_active: Boolean(cloudRetentionActive),
      locations_checked: parseList(cloudLocationsChecked),
      evidence_complete: Boolean(cloudEvidenceComplete),
    };

    console.log("VANISH Cloud Verification Payload:", payload);

    try {
      const result = await api.verifyCloudDeletion(payload);

      console.log("VANISH Cloud Verification Response:", result);

      setCloudResult(result);
    } catch (error) {
      console.error("Cloud Verification Error:", error);

      setCloudError(
        error.message || "Cloud verification failed."
      );
    } finally {
      setCloudLoading(false);
    }
  }
  // =========================================================
  // CHAIN OF CUSTODY DATA
  // =========================================================

  const loadCustodyData = useCallback(async () => {
    setCustodyLoading(true);
    setCustodyError("");

    try {
      const [eventsResult, verificationResult] =
        await Promise.all([
          custodyAuditFilter
            ? api.custodyEventsByAudit(custodyAuditFilter)
            : api.custodyEvents(),
          api.verifyCustodyChain(),
        ]);

      const events = getArray(eventsResult);

      setCustodyEventsList(events);
      setCustodyCount(
        typeof eventsResult?.total === "number"
          ? eventsResult.total
          : events.length
      );

      setCustodyVerification(verificationResult);
      setChainStatus(getChainStatus(verificationResult));
    } catch (error) {
      setCustodyError(
        error.message || "Failed to load custody records."
      );
    } finally {
      setCustodyLoading(false);
    }
  }, [custodyAuditFilter]);
    useEffect(() => {
    if (activePage === "Chain of Custody") {
      loadCustodyData();
    }
  }, [activePage, loadCustodyData]);

// =========================================================
// EVIDENCE PAGE
// =========================================================

function EvidencePage({
  records,
  totalRecords,
  loading,
  error,
  search,
  setSearch,
  scanLoading,
  uploadLoading,
  selectedFile,
  setSelectedFile,
  onScan,
  onUpload,
  onRefresh,
  message,
  messageType,
}) {
  return (
    <>
      <section className="welcome-section evidence-welcome">
        <div>
          <div className="eyebrow">FORENSIC EVIDENCE MANAGEMENT</div>

          <h1>Evidence</h1>

          <p className="welcome-description">
            Collect files, generate cryptographic hashes,
            and maintain digital evidence records.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={onScan}
          disabled={scanLoading || loading}
        >
          <Icon name="search" size={18} />
          {scanLoading ? "Scanning..." : "Scan Evidence Folder"}
        </button>
      </section>

      {/* EVIDENCE STATISTICS */}
      <section className="evidence-stats-grid">
        <div className="evidence-mini-card">
          <span className="evidence-mini-icon">
            <Icon name="folder" size={20} />
          </span>

          <div>
            <strong>{totalRecords}</strong>
            <span>Total Records</span>
          </div>
        </div>

        <div className="evidence-mini-card">
          <span className="evidence-mini-icon">
            <Icon name="shield" size={20} />
          </span>

          <div>
            <strong>SHA-256</strong>
            <span>Hash Algorithm</span>
          </div>
        </div>

        <div className="evidence-mini-card">
          <span className="evidence-mini-icon">
            <Icon name="activity" size={20} />
          </span>

          <div>
            <strong>Automated</strong>
            <span>Evidence Collection</span>
          </div>
        </div>
      </section>

      {/* UPLOAD EVIDENCE */}
      <section className="panel evidence-upload-panel">
        <div className="panel-header">
          <div>
            <h2>Upload Evidence</h2>
            <p>Upload an individual file for forensic collection</p>
          </div>
        </div>

        <div className="evidence-upload-controls">
          <label className="evidence-file-input-wrapper">
            <input
              id="evidence-file-input"
              type="file"
              onChange={(event) =>
                setSelectedFile(event.target.files?.[0] || null)
              }
            />

            <Icon name="upload" size={19} />

            <span>
              {selectedFile
                ? selectedFile.name
                : "Choose a file to upload"}
            </span>
          </label>

          <button
            className="primary-button"
            onClick={onUpload}
            disabled={!selectedFile || uploadLoading}
          >
            <Icon name="upload" size={17} />
            {uploadLoading ? "Uploading..." : "Upload Evidence"}
          </button>
        </div>

        {selectedFile && (
          <div className="selected-file-info">
            Selected file: {formatBytes(selectedFile.size)}
          </div>
        )}
      </section>

      {/* MESSAGES */}
      {message && (
        <div className={`evidence-message ${messageType}`}>
          <Icon name="check" size={18} />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="evidence-message error">
          <span>{error}</span>
        </div>
      )}

      {/* EVIDENCE RECORDS */}
      <section className="panel evidence-table-panel">
        <div className="panel-header evidence-table-header">
          <div>
            <h2>Evidence Records</h2>
            <p>Collected files and forensic metadata</p>
          </div>

          <button
            className="secondary-button"
            onClick={onRefresh}
            disabled={loading}
          >
            <Icon name="refresh" size={16} />
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {/* SEARCH */}
        <div className="evidence-search-wrapper">
          <Icon name="search" size={18} />

          <input
            type="text"
            placeholder="Search filename, hash, or Audit ID..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {/* LOADING */}
        {loading ? (
          <div className="evidence-table-state">
            <div className="loading-indicator" />
            <p>Loading evidence records...</p>
          </div>
        ) : records.length === 0 ? (
          /* EMPTY STATE */
          <div className="evidence-table-state">
            <div className="overview-icon">
              <Icon name="folder" size={25} />
            </div>

            <h3>No evidence records found</h3>

            <p>
              {search
                ? "Try changing your search."
                : "Upload a file or scan the evidence folder to begin."}
            </p>
          </div>
        ) : (
          /* TABLE */
          <div className="evidence-table-scroll">
            <table className="evidence-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Size</th>
                  <th>Collected</th>
                  <th>SHA-256</th>
                  <th>Status</th>
                  <th>Audit ID</th>
                </tr>
              </thead>

              <tbody>
                {records.map((record, index) => {
                  const originalFileName =
                    record.file_name ||
                    record.filename ||
                    record.relative_path ||
                    "Unnamed file";

                  // Fix duplicate extensions for display only
                  let fileName = originalFileName;

                  while (/\.(\w+)\.\1$/i.test(fileName)) {
                    fileName = fileName.replace(
                      /\.(\w+)\.\1$/i,
                      ".$1"
                    );
                  }

                  const hash =
                    record.sha256 ||
                    record.hash ||
                    "—";

                  const auditId =
                    record.audit_id ||
                    record.auditId ||
                    "—";

                  const extension =
                    record.extension ||
                    fileName.split(".").pop();

                  return (
                    <tr
                      key={
                        record.id ||
                        record.evidence_id ||
                        `${auditId}-${index}`
                      }
                    >
                      {/* FILE NAME */}
                      <td>
                        <div className="evidence-file-cell">
                          <span className="evidence-file-icon">
                            <Icon name="file" size={17} />
                          </span>

                          <div>
                            <strong title={fileName}>
                              {fileName}
                            </strong>

                            <span>{extension}</span>
                          </div>
                        </div>
                      </td>

                      {/* SIZE */}
                      <td>
                        {formatBytes(
                          record.file_size ?? record.size
                        )}
                      </td>

                      {/* COLLECTION TIME */}
                      <td>
                        {formatDate(
                          record.collection_time ||
                          record.collected_at ||
                          record.created_at
                        )}
                      </td>

                      {/* HASH */}
                      <td>
                        <button
                          className="hash-copy-button"
                          title="Click to copy full hash"
                          onClick={() =>
                            navigator.clipboard
                              .writeText(String(hash))
                              .catch(() => {})
                          }
                        >
                          {hash === "—"
                            ? "—"
                            : `${String(hash).slice(0, 12)}...`}
                        </button>
                      </td>

                      {/* STATUS */}
                      <td>
                        <span className="evidence-status">
                          {record.status || "Collected"}
                        </span>
                      </td>

                      {/* AUDIT ID */}
                      <td>
                        <span
                          className="audit-id-cell"
                          title={auditId}
                        >
                          {auditId === "—"
                            ? "—"
                            : `${String(auditId).slice(0, 8)}...`}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* FOOTER */}
        <div className="evidence-table-footer">
          Showing {records.length} of {totalRecords} evidence records
        </div>
      </section>
    </>
  );
}

  // =========================================================
  // INTEGRITY VERIFICATION PAGE
  // =========================================================

  function IntegrityPage({
    records,
    selectedAuditId,
    setSelectedAuditId,
    loading,
    verifying,
    error,
    result,
    onVerify,
    onRefresh,
  }) {
    const auditRecords = records.filter(
      (record) => record.audit_id
    );

    const uniqueAuditIds = [
      ...new Map(
        auditRecords.map((record) => [
          record.audit_id,
          record,
        ])
      ).values(),
    ];

    const resultFiles = result?.results || [];
    const analysis = result?.forensic_analysis || {};
    const statistics = analysis.statistics || result || {};

    const overallStatus = result?.overall_status || "";
    const isVerified = overallStatus === "INTEGRITY_VERIFIED";

    return (
      <>
        <section className="welcome-section integrity-welcome">
          <div>
            <div className="eyebrow">
              CRYPTOGRAPHIC EVIDENCE VALIDATION
            </div>

            <h1>Integrity Verification</h1>

            <p className="welcome-description">
              Verify evidence integrity by comparing stored SHA-256
              hashes against the current files.
            </p>
          </div>

          <button
            className="secondary-button"
            onClick={onRefresh}
            disabled={loading || verifying}
          >
            <Icon name="refresh" size={17} />
            {loading ? "Loading..." : "Refresh Evidence"}
          </button>
        </section>

        <section className="panel integrity-select-panel">
          <div className="panel-header">
            <div>
              <h2>Select Evidence for Verification</h2>
              <p>
                Choose an Audit ID to perform cryptographic verification.
              </p>
            </div>
          </div>

          <div className="integrity-selection-controls">
            <div className="integrity-select-wrapper">
              <label htmlFor="integrity-audit-select">
                Evidence Audit ID
              </label>

              <select
                id="integrity-audit-select"
                value={selectedAuditId}
                onChange={(event) => {
                  setSelectedAuditId(event.target.value);
                }}
                disabled={loading || uniqueAuditIds.length === 0}
              >
                <option value="">
                  {loading
                    ? "Loading evidence records..."
                    : "Select an Audit ID"}
                </option>

                {uniqueAuditIds.map((record) => (
                  <option
                    key={record.audit_id}
                    value={record.audit_id}
                  >
                    {record.file_name ||
                      record.filename ||
                      record.relative_path ||
                      "Evidence file"}{" "}
                    — {record.audit_id}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="primary-button integrity-verify-button"
              onClick={onVerify}
              disabled={verifying || loading || !selectedAuditId}
            >
              <Icon name="shield" size={18} />
              {verifying
                ? "Verifying Integrity..."
                : "Verify Integrity"}
            </button>
          </div>

          {selectedAuditId && (
            <div className="integrity-selected-id">
              <span>Selected Audit ID</span>
              <code>{selectedAuditId}</code>
            </div>
          )}
        </section>

        {error && (
          <div className="evidence-message error">
            <span>{error}</span>
          </div>
        )}

        {verifying && (
          <section className="panel integrity-loading-panel">
            <div className="loading-indicator" />
            <h3>Verifying evidence integrity...</h3>
            <p>
              Calculating current file hashes and comparing them
              with the stored reference hashes.
            </p>
          </section>
        )}

        {result && !verifying && (
          <>
            <section
              className={`integrity-result-banner ${
                isVerified ? "verified" : "failed"
              }`}
            >
              <div className="integrity-result-icon">
                <Icon
                  name={isVerified ? "shield" : "activity"}
                  size={29}
                />
              </div>

              <div className="integrity-result-content">
                <span className="integrity-result-label">
                  VERIFICATION RESULT
                </span>

                <h2>
                  {isVerified
                    ? "Integrity Verified"
                    : overallStatus.replaceAll("_", " ") ||
                      "Verification Completed"}
                </h2>

                <p>
                  {analysis.summary ||
                    "Verification results are available below."}
                </p>
              </div>

              <div className="integrity-result-badge">
                {isVerified ? "VERIFIED" : "REVIEW"}
              </div>
            </section>

            <section className="integrity-stats-grid">
              <IntegrityStat
                label="Total Files"
                value={result.total_files ?? statistics.total_files ?? 0}
                icon="file"
              />

              <IntegrityStat
                label="Intact"
                value={result.intact ?? statistics.intact ?? 0}
                icon="shield"
                variant="success"
              />

              <IntegrityStat
                label="Modified"
                value={result.modified ?? statistics.modified ?? 0}
                icon="activity"
                variant="danger"
              />

              <IntegrityStat
                label="Missing"
                value={result.missing ?? statistics.missing ?? 0}
                icon="folder"
                variant="warning"
              />

              <IntegrityStat
                label="Invalid"
                value={result.invalid ?? statistics.invalid ?? 0}
                icon="file"
                variant="danger"
              />
            </section>

            <section className="panel integrity-analysis-panel">
              <div className="panel-header">
                <div>
                  <h2>Forensic Analysis</h2>
                  <p>Automated assessment of verification results</p>
                </div>

                <span
                  className={`integrity-risk-badge ${
                    String(analysis.risk_level || "unknown").toLowerCase()
                  }`}
                >
                  {analysis.risk_level || "Unknown"} Risk
                </span>
              </div>

              <div className="integrity-analysis-grid">
                <div className="integrity-analysis-metric">
                  <span>Risk Score</span>
                  <strong>{analysis.risk_score ?? "—"}</strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Analysis Status</span>
                  <strong>{analysis.analysis_status || "—"}</strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Analysis Type</span>
                  <strong className="analysis-type-text">
                    {analysis.analysis_type
                      ? analysis.analysis_type.replaceAll("_", " ")
                      : "—"}
                  </strong>
                </div>
              </div>

              {analysis.recommendations?.length > 0 && (
                <div className="integrity-recommendations">
                  <h3>Recommendations</h3>

                  {analysis.recommendations.map(
                    (recommendation, index) => (
                      <div
                        className="integrity-recommendation"
                        key={index}
                      >
                        <Icon name="check" size={17} />
                        <span>{recommendation}</span>
                      </div>
                    )
                  )}
                </div>
              )}
            </section>

            <section className="panel integrity-results-panel">
              <div className="panel-header">
                <div>
                  <h2>File Verification Details</h2>
                  <p>
                    Individual file integrity results and hash comparison
                  </p>
                </div>
              </div>

              {resultFiles.length === 0 ? (
                <div className="evidence-table-state">
                  <p>No individual file results were returned.</p>
                </div>
              ) : (
                <div className="integrity-results-list">
                  {resultFiles.map((file, index) => {
                    const fileStatus = String(
                      file.status || "unknown"
                    ).toLowerCase();

                    const intact =
                      file.integrity_verified === true ||
                      fileStatus === "intact";

                    return (
                      <div
                        className="integrity-file-card"
                        key={`${file.file_path || file.file_name}-${index}`}
                      >
                        <div className="integrity-file-header">
                          <div className="integrity-file-info">
                            <span className="evidence-file-icon">
                              <Icon name="file" size={18} />
                            </span>

                            <div>
                              <strong>
                                {file.file_name ||
                                  file.filename ||
                                  file.relative_path ||
                                  "Unnamed file"}
                              </strong>

                              <span>
                                {file.relative_path ||
                                  file.file_path ||
                                  "Path unavailable"}
                              </span>
                            </div>
                          </div>

                          <span
                            className={`integrity-file-status ${
                              intact ? "intact" : fileStatus
                            }`}
                          >
                            {file.status || "Unknown"}
                          </span>
                        </div>

                        <div className="integrity-hash-grid">
                          <div className="integrity-hash-block">
                            <span>Expected SHA-256</span>
                            <code>
                              {file.expected_hash || "Unavailable"}
                            </code>
                          </div>

                          <div className="integrity-hash-block">
                            <span>Actual SHA-256</span>
                            <code>
                              {file.actual_hash || "Unavailable"}
                            </code>
                          </div>
                        </div>

                        <div className="integrity-hash-comparison">
                          <Icon
                            name={intact ? "check" : "activity"}
                            size={17}
                          />

                          <span>
                            {intact
                              ? "Stored and current hashes match."
                              : "Hash mismatch or file verification issue detected."}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="evidence-table-footer">
                Audit ID: {result.audit_id || selectedAuditId}
              </div>
            </section>
          </>
        )}

        {!result && !error && !verifying && (
          <section className="panel integrity-empty-panel">
            <div className="placeholder-page-icon">
              <Icon name="shield" size={30} />
            </div>

            <h2>Ready to Verify</h2>

            <p>
              Select an evidence record above and click
              <strong> Verify Integrity </strong>
              to begin the SHA-256 integrity assessment.
            </p>
          </section>
        )}
      </>
    );
  }

  // =========================================================
  // SANITIZATION PAGE
  // =========================================================

  function SanitizationPage({
    records,
    loading,
    verifying,
    target,
    setTarget,
    method,
    setMethod,
    storageType,
    setStorageType,
    residualMarker,
    setResidualMarker,
    error,
    result,
    onVerify,
    onRefresh,
  }) {
    const getRecordPath = (record) =>
      record.file_path ||
      record.absolute_path ||
      record.full_path ||
      record.target_path ||
      record.path ||
      "";

    const testFiles = records.filter((record) => {
      const path = String(getRecordPath(record)).toLowerCase();

      return path.includes("test_files");
    });

    const getFileName = (record) =>
      record.file_name ||
      record.filename ||
      record.relative_path ||
      getRecordPath(record).split(/[\\/]/).pop() ||
      "Unnamed file";

    const report = result?.report_generation || {};

    const verificationStatus =
      result?.status ||
      result?.verification_status ||
      result?.overall_status ||
      "Completed";

    const resultDetails = result
      ? Object.entries(result).filter(
          ([key]) =>
            ![
              "report_generation",
              "verification_id",
              "status",
              "verification_status",
              "overall_status",
            ].includes(key)
        )
      : [];

    return (
      <>
        <section className="welcome-section">
          <div>
            <div className="eyebrow">
              DATA ERASURE ASSESSMENT
            </div>

            <h1>Sanitization Verification</h1>

            <p className="welcome-description">
              Evaluate sanitization evidence and assess whether
              residual data indicators remain in the selected target.
            </p>
          </div>

          <button
            className="secondary-button"
            onClick={onRefresh}
            disabled={loading || verifying}
          >
            <Icon name="refresh" size={17} />
            {loading ? "Loading..." : "Refresh Evidence"}
          </button>
        </section>

        <section className="panel integrity-select-panel">
          <div className="panel-header">
            <div>
              <h2>Sanitization Verification Setup</h2>
              <p>
                Select a permitted test file and configure the
                verification parameters.
              </p>
            </div>
          </div>

          <div className="sanitization-form">
            <div className="sanitization-field">
              <label htmlFor="sanitization-file-select">
                Evidence Test File
              </label>

              <select
                id="sanitization-file-select"
                value={target}
                onChange={(event) => setTarget(event.target.value)}
                disabled={loading || verifying}
              >
                <option value="">
                  {loading
                    ? "Loading evidence records..."
                    : "Select a test evidence file"}
                </option>

                {testFiles.map((record, index) => {
                  const path = getRecordPath(record);

                  return (
                    <option
                      key={
                        record.id ||
                        record.audit_id ||
                        `${path}-${index}`
                      }
                      value={path}
                    >
                      {getFileName(record)}
                    </option>
                  );
                })}
              </select>

              <p className="sanitization-field-hint">
                Only files located within the backend test_files
                directory are accepted.
              </p>
            </div>

            <div className="sanitization-field">
              <label htmlFor="sanitization-target-path">
                Target File Path
              </label>

              <input
                id="sanitization-target-path"
                type="text"
                value={target}
                onChange={(event) => setTarget(event.target.value)}
                placeholder="Enter permitted test file path"
                disabled={verifying}
              />

              <p className="sanitization-field-hint">
                You can select a file above or enter its full path manually.
              </p>
            </div>

            <div className="sanitization-field">
              <label htmlFor="sanitization-method">
                Sanitization Method
              </label>

              <input
                id="sanitization-method"
                type="text"
                value={method}
                onChange={(event) => setMethod(event.target.value)}
                placeholder="e.g. overwrite, secure_delete"
                disabled={verifying}
              />
            </div>

            <div className="sanitization-field">
              <label htmlFor="sanitization-storage">
                Storage Type
              </label>

              <input
                id="sanitization-storage"
                type="text"
                value={storageType}
                onChange={(event) =>
                  setStorageType(event.target.value)
                }
                placeholder="e.g. filesystem, HDD, SSD"
                disabled={verifying}
              />
            </div>

            <div className="sanitization-field sanitization-full-width">
              <label htmlFor="sanitization-marker">
                Residual Marker (Optional)
              </label>

              <input
                id="sanitization-marker"
                type="text"
                value={residualMarker}
                onChange={(event) =>
                  setResidualMarker(event.target.value)
                }
                placeholder="Enter a known test marker to search for"
                disabled={verifying}
              />

              <p className="sanitization-field-hint">
                Use a marker that was deliberately placed in a test file
                for your experiment.
              </p>
            </div>
          </div>

          <div className="sanitization-form-actions">
            <button
              className="primary-button"
              onClick={onVerify}
              disabled={verifying || loading || !target.trim()}
            >
              <Icon name="shield" size={18} />
              {verifying
                ? "Verifying Sanitization..."
                : "Run Sanitization Verification"}
            </button>
          </div>
        </section>

        {error && (
          <div className="evidence-message error">
            <span>{error}</span>
          </div>
        )}

        {verifying && (
          <section className="panel integrity-loading-panel">
            <div className="loading-indicator" />

            <h3>Analyzing sanitization...</h3>

            <p>
              Checking the selected target and generating the
              sanitization verification report.
            </p>
          </section>
        )}

        {result && !verifying && (
          <>
            <section className="integrity-result-banner">
              <div className="integrity-result-icon">
                <Icon name="trash" size={29} />
              </div>

              <div className="integrity-result-content">
                <span className="integrity-result-label">
                  SANITIZATION ASSESSMENT
                </span>

                <h2>
                  {String(verificationStatus).replaceAll("_", " ")}
                </h2>

                <p>
                  Verification analysis has completed.
                  Review the returned assessment and report details.
                </p>
              </div>

              <div className="integrity-result-badge">
                COMPLETED
              </div>
            </section>

            <section className="integrity-stats-grid sanitization-stats-grid">
              <IntegrityStat
                label="Verification ID"
                value={
                  result.verification_id
                    ? String(result.verification_id).slice(0, 8)
                    : "—"
                }
                icon="file"
              />

              <IntegrityStat
                label="Status"
                value={verificationStatus}
                icon="shield"
              />

              <IntegrityStat
                label="Report"
                value={report.report_status || "—"}
                icon="file"
              />

              <IntegrityStat
                label="Custody"
                value={report.custody_status || "—"}
                icon="link"
              />
            </section>

            <section className="panel integrity-analysis-panel">
              <div className="panel-header">
                <div>
                  <h2>Verification Details</h2>
                  <p>Sanitization assessment information</p>
                </div>
              </div>

              <div className="integrity-analysis-grid">
                <div className="integrity-analysis-metric">
                  <span>Target File</span>
                  <strong className="analysis-type-text">
                    {result.target_path || target || "—"}
                  </strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Method</span>
                  <strong>
                    {result.sanitization_method || method || "—"}
                  </strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Storage Type</span>
                  <strong>
                    {result.storage_type || storageType || "—"}
                  </strong>
                </div>
              </div>

              {result.summary && (
                <div className="integrity-recommendations">
                  <h3>Summary</h3>

                  <div className="integrity-recommendation">
                    <Icon name="activity" size={17} />
                    <span>{result.summary}</span>
                  </div>
                </div>
              )}
            </section>

            {resultDetails.length > 0 && (
              <section className="panel integrity-results-panel">
                <div className="panel-header">
                  <div>
                    <h2>Assessment Results</h2>
                    <p>Details returned by the verification engine</p>
                  </div>
                </div>

                <div className="sanitization-result-details">
                  {resultDetails.map(([key, value]) => (
                    <div
                      className="sanitization-detail-row"
                      key={key}
                    >
                      <strong>
                        {key.replaceAll("_", " ")}
                      </strong>

                      <span>
                        {typeof value === "object" && value !== null
                          ? JSON.stringify(value, null, 2)
                          : String(value ?? "—")}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="panel integrity-analysis-panel">
              <div className="panel-header">
                <div>
                  <h2>Report Generation</h2>
                  <p>Automatically generated verification report</p>
                </div>
              </div>

              <div className="integrity-analysis-grid">
                <div className="integrity-analysis-metric">
                  <span>Report Status</span>
                  <strong>
                    {report.report_status || "Not available"}
                  </strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Hash Algorithm</span>
                  <strong>
                    {report.hash_algorithm || "—"}
                  </strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Custody Status</span>
                  <strong>
                    {report.custody_status || "—"}
                  </strong>
                </div>
              </div>

              {report.report_path && (
                <div className="integrity-recommendations">
                  <h3>Report Path</h3>

                  <div className="integrity-hash-block">
                    <code>{report.report_path}</code>
                  </div>
                </div>
              )}

              {report.report_hash && (
                <div className="integrity-recommendations">
                  <h3>Report Hash</h3>

                  <div className="integrity-hash-block">
                    <code>{report.report_hash}</code>
                  </div>
                </div>
              )}

              {report.error && (
                <div className="evidence-message error">
                  {report.error}
                </div>
              )}
            </section>

            <div className="sanitization-disclaimer">
              <Icon name="activity" size={18} />

              <p>
                <strong>Forensic limitation:</strong> A verification
                result is an assessment based on the checks performed
                by this prototype. It does not independently prove
                physical destruction or complete erasure of all
                storage media.
              </p>
            </div>
          </>
        )}

        {!result && !error && !verifying && (
          <section className="panel integrity-empty-panel">
            <div className="placeholder-page-icon">
              <Icon name="trash" size={30} />
            </div>

            <h2>Ready for Sanitization Assessment</h2>

            <p>
              Select a test file, configure the verification parameters,
              and run the sanitization assessment.
            </p>
          </section>
        )}
      </>
    );
  }

  // =========================================================
  // CLOUD VERIFICATION PAGE
  // =========================================================

  function CloudVerificationPage({
    deletionConfirmed,
    setDeletionConfirmed,
    residualObjects,
    setResidualObjects,
    retainedVersions,
    setRetainedVersions,
    backupCopies,
    setBackupCopies,
    retentionActive,
    setRetentionActive,
    locationsChecked,
    setLocationsChecked,
    evidenceComplete,
    setEvidenceComplete,
    loading,
    error,
    result,
    onVerify,
  }) {
    const parseList = (value) =>
      String(value || "")
        .split(/[\n,]+/)
        .map((item) => item.trim())
        .filter(Boolean);

    const statistics = result?.statistics || {};

    const findings = Array.isArray(result?.findings)
      ? result.findings
      : [];

    const recommendations = Array.isArray(result?.recommendations)
      ? result.recommendations
      : [];

    const status = String(
      result?.verification_status || "UNKNOWN"
    ).toUpperCase();

    const risk = String(
      result?.risk_level || "UNKNOWN"
    ).toUpperCase();

    const passed =
      status === "PASSED" ||
      status === "VERIFIED" ||
      status === "SUCCESS";

    const statusClass = passed ? "verified" : "failed";
    const riskClass = risk.toLowerCase();

    return (
      <>
        <section className="welcome-section">
          <div>
            <div className="eyebrow">
              CLOUD DATA DELETION ASSESSMENT
            </div>

            <h1>Cloud Verification</h1>

            <p className="welcome-description">
              Assess cloud deletion evidence, residual objects,
              retained versions, backups, and storage locations.
            </p>
          </div>
        </section>

        <section className="panel integrity-select-panel">
          <div className="panel-header">
            <div>
              <h2>Cloud Verification Setup</h2>
              <p>
                Enter the available evidence from the cloud deletion
                operation. This assessment uses submitted evidence
                and does not connect directly to a cloud provider.
              </p>
            </div>
          </div>

          <div className="sanitization-form">
            <div className="sanitization-field sanitization-full-width">
              <label>Deletion Confirmation</label>

              <label className="cloud-checkbox-label">
                <input
                  type="checkbox"
                  checked={deletionConfirmed}
                  onChange={(event) =>
                    setDeletionConfirmed(event.target.checked)
                  }
                  disabled={loading}
                />

                <span>
                  Deletion was confirmed by available evidence
                </span>
              </label>
            </div>

            <div className="sanitization-field sanitization-full-width">
              <label htmlFor="cloud-residual-objects">
                Residual Objects
              </label>

              <textarea
                id="cloud-residual-objects"
                value={residualObjects}
                onChange={(event) =>
                  setResidualObjects(event.target.value)
                }
                placeholder={
                  "Enter residual object identifiers, one per line\nExample: residual_object_1"
                }
                disabled={loading}
              />

              <p className="sanitization-field-hint">
                Enter object names or identifiers found after deletion.
                Leave blank if none were identified.
              </p>
            </div>

            <div className="sanitization-field sanitization-full-width">
              <label htmlFor="cloud-retained-versions">
                Retained Versions
              </label>

              <textarea
                id="cloud-retained-versions"
                value={retainedVersions}
                onChange={(event) =>
                  setRetainedVersions(event.target.value)
                }
                placeholder={
                  "Enter retained version identifiers, one per line"
                }
                disabled={loading}
              />
            </div>

            <div className="sanitization-field sanitization-full-width">
              <label htmlFor="cloud-backup-copies">
                Backup Copies
              </label>

              <textarea
                id="cloud-backup-copies"
                value={backupCopies}
                onChange={(event) =>
                  setBackupCopies(event.target.value)
                }
                placeholder={
                  "Enter backup copy identifiers, one per line"
                }
                disabled={loading}
              />
            </div>

            <div className="sanitization-field sanitization-full-width">
              <label>Retention Policy</label>

              <label className="cloud-checkbox-label">
                <input
                  type="checkbox"
                  checked={retentionActive}
                  onChange={(event) =>
                    setRetentionActive(event.target.checked)
                  }
                  disabled={loading}
                />

                <span>
                  Retention policy is active and may retain data
                </span>
              </label>
            </div>

            <div className="sanitization-field sanitization-full-width">
              <label htmlFor="cloud-locations-checked">
                Storage Locations Checked
              </label>

              <textarea
                id="cloud-locations-checked"
                value={locationsChecked}
                onChange={(event) =>
                  setLocationsChecked(event.target.value)
                }
                placeholder={
                  "Enter storage locations checked, one per line\nExample: primary_storage\nExample: backup_storage"
                }
                disabled={loading}
              />

              <p className="sanitization-field-hint">
                Separate multiple locations with commas or new lines.
              </p>
            </div>

            <div className="sanitization-field sanitization-full-width">
              <label>Evidence Completeness</label>

              <label className="cloud-checkbox-label">
                <input
                  type="checkbox"
                  checked={evidenceComplete}
                  onChange={(event) =>
                    setEvidenceComplete(event.target.checked)
                  }
                  disabled={loading}
                />

                <span>
                  Available evidence is considered complete for this assessment
                </span>
              </label>
            </div>
          </div>

          <div className="sanitization-form-actions">
            <button
              className="primary-button"
              onClick={onVerify}
              disabled={loading}
            >
              <Icon name="cloud" size={18} />

              {loading
                ? "Analyzing Cloud Evidence..."
                : "Run Cloud Verification"}
            </button>
          </div>
        </section>

        {error && (
          <div className="evidence-message error">
            <span>{error}</span>
          </div>
        )}

        {loading && (
          <section className="panel integrity-loading-panel">
            <div className="loading-indicator" />

            <h3>Analyzing cloud deletion evidence...</h3>

            <p>
              Evaluating deletion confirmation, residual objects,
              retained versions, backup copies, retention policies,
              and evidence completeness.
            </p>
          </section>
        )}

        {result && !loading && (
          <>
            <section
              className={`integrity-result-banner ${statusClass}`}
            >
              <div className="integrity-result-icon">
                <Icon
                  name={passed ? "shield" : "cloud"}
                  size={29}
                />
              </div>

              <div className="integrity-result-content">
                <span className="integrity-result-label">
                  CLOUD VERIFICATION RESULT
                </span>

                <h2>{status.replaceAll("_", " ")}</h2>

                <p>
                  {result.summary ||
                    "Cloud deletion assessment has completed."}
                </p>
              </div>

              <div className="integrity-result-badge">
                {status.replaceAll("_", " ")}
              </div>
            </section>

            <section className="integrity-stats-grid">
              <IntegrityStat
                label="Residual Objects"
                value={statistics.residual_objects ?? 0}
                icon="file"
                variant={
                  Number(statistics.residual_objects || 0) > 0
                    ? "danger"
                    : "success"
                }
              />

              <IntegrityStat
                label="Retained Versions"
                value={statistics.retained_versions ?? 0}
                icon="activity"
                variant={
                  Number(statistics.retained_versions || 0) > 0
                    ? "warning"
                    : "success"
                }
              />

              <IntegrityStat
                label="Backup Copies"
                value={statistics.backup_copies ?? 0}
                icon="folder"
                variant={
                  Number(statistics.backup_copies || 0) > 0
                    ? "warning"
                    : "success"
                }
              />

              <IntegrityStat
                label="Locations Checked"
                value={statistics.locations_checked ?? 0}
                icon="cloud"
              />

              <IntegrityStat
                label="Evidence Complete"
                value={
                  statistics.evidence_complete === true
                    ? "Yes"
                    : statistics.evidence_complete === false
                    ? "No"
                    : "—"
                }
                icon="shield"
                variant={
                  statistics.evidence_complete === true
                    ? "success"
                    : "warning"
                }
              />
            </section>

            <section className="panel integrity-analysis-panel">
              <div className="panel-header">
                <div>
                  <h2>Risk Assessment</h2>
                  <p>Cloud deletion verification analysis</p>
                </div>

                <span
                  className={`integrity-risk-badge ${riskClass}`}
                >
                  {risk} Risk
                </span>
              </div>

              <div className="integrity-analysis-grid">
                <div className="integrity-analysis-metric">
                  <span>Verification Status</span>
                  <strong>{status.replaceAll("_", " ")}</strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Risk Level</span>
                  <strong>{risk}</strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Analysis Status</span>
                  <strong>
                    {result.analysis_status || "—"}
                  </strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Analysis Type</span>
                  <strong className="analysis-type-text">
                    {result.analysis_type
                      ? result.analysis_type.replaceAll("_", " ")
                      : "—"}
                  </strong>
                </div>

                <div className="integrity-analysis-metric">
                  <span>Verification ID</span>
                  <strong className="analysis-type-text">
                    {result.verification_id || "—"}
                  </strong>
                </div>
              </div>
            </section>

            <section className="panel integrity-results-panel">
              <div className="panel-header">
                <div>
                  <h2>Findings</h2>
                  <p>
                    Issues identified during cloud deletion assessment
                  </p>
                </div>
              </div>

              {findings.length === 0 ? (
                <div className="evidence-table-state">
                  <Icon name="check" size={24} />
                  <h3>No findings returned</h3>
                  <p>
                    The analysis did not return any specific findings.
                  </p>
                </div>
              ) : (
                <div className="integrity-results-list">
                  {findings.map((finding, index) => (
                    <div
                      className="integrity-file-card"
                      key={finding.finding_id || index}
                    >
                      <div className="integrity-file-header">
                        <div className="integrity-file-info">
                          <span className="evidence-file-icon">
                            <Icon name="activity" size={18} />
                          </span>

                          <div>
                            <strong>
                              {String(
                                finding.finding_id ||
                                  finding.title ||
                                  `Finding ${index + 1}`
                              ).replaceAll("_", " ")}
                            </strong>

                            <span>
                              {finding.description ||
                                "No description provided."}
                            </span>
                          </div>
                        </div>

                        <span
                          className={`integrity-file-status ${
                            String(
                              finding.severity || "unknown"
                            ).toLowerCase()
                          }`}
                        >
                          {finding.severity || "Unspecified"}
                        </span>
                      </div>

                      {finding.count !== undefined && (
                        <div className="integrity-hash-comparison">
                          <Icon name="activity" size={17} />
                          <span>
                            Count: {finding.count}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="panel integrity-analysis-panel">
              <div className="panel-header">
                <div>
                  <h2>Recommendations</h2>
                  <p>
                    Suggested actions based on the analysis
                  </p>
                </div>
              </div>

              {recommendations.length === 0 ? (
                <div className="evidence-table-state">
                  <p>No recommendations were returned.</p>
                </div>
              ) : (
                <div className="integrity-recommendations">
                  {recommendations.map((recommendation, index) => (
                    <div
                      className="integrity-recommendation"
                      key={index}
                    >
                      <Icon name="check" size={17} />
                      <span>{recommendation}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="panel integrity-analysis-panel">
              <div className="panel-header">
                <div>
                  <h2>Submitted Evidence Parameters</h2>
                  <p>Values used in this verification request</p>
                </div>
              </div>

              <div className="sanitization-result-details">
                <div className="sanitization-detail-row">
                  <strong>Deletion Confirmed</strong>
                  <span>{deletionConfirmed ? "Yes" : "No"}</span>
                </div>

                <div className="sanitization-detail-row">
                  <strong>Retention Active</strong>
                  <span>{retentionActive ? "Yes" : "No"}</span>
                </div>

                <div className="sanitization-detail-row">
                  <strong>Evidence Complete</strong>
                  <span>{evidenceComplete ? "Yes" : "No"}</span>
                </div>

                <div className="sanitization-detail-row">
                  <strong>Residual Objects Submitted</strong>
                  <span>
                    {parseList(residualObjects).length}
                  </span>
                </div>

                <div className="sanitization-detail-row">
                  <strong>Retained Versions Submitted</strong>
                  <span>
                    {parseList(retainedVersions).length}
                  </span>
                </div>

                <div className="sanitization-detail-row">
                  <strong>Backup Copies Submitted</strong>
                  <span>
                    {parseList(backupCopies).length}
                  </span>
                </div>

                <div className="sanitization-detail-row">
                  <strong>Locations Submitted</strong>
                  <span>
                    {parseList(locationsChecked).join(", ") || "None"}
                  </span>
                </div>
              </div>
            </section>

            <div className="sanitization-disclaimer">
              <Icon name="activity" size={18} />

              <p>
                <strong>Forensic limitation:</strong> This module
                performs rules-based analysis of submitted evidence.
                It does not directly access cloud services, verify
                provider infrastructure, or independently prove
                physical deletion of all cloud data.
              </p>
            </div>
          </>
        )}

        {!result && !error && !loading && (
          <section className="panel integrity-empty-panel">
            <div className="placeholder-page-icon">
              <Icon name="cloud" size={30} />
            </div>

            <h2>Ready for Cloud Assessment</h2>

            <p>
              Enter the available deletion evidence above and run
              cloud verification to receive a risk assessment,
              findings, and recommendations.
            </p>
          </section>
        )}
      </>
    );
  }

  // =========================================================
  // SHARED COMPONENTS
  // =========================================================

  function IntegrityStat({
    label,
    value,
    icon,
    variant = "",
  }) {
    return (
      <div className={`integrity-stat-card ${variant}`}>
        <div className="integrity-stat-top">
          <span className="integrity-stat-icon">
            <Icon name={icon} size={19} />
          </span>
        </div>

        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    );
  }

  function StatCard({ title, value, icon, note }) {
    return (
      <div className="stat-card">
        <div className="stat-top">
          <span className="stat-icon">
            <Icon name={icon} size={19} />
          </span>

          <span className="stat-note">{note}</span>
        </div>

        <div className="stat-value">{value}</div>
        <div className="stat-title">{title}</div>
      </div>
    );
  }

  function QuickAction({
    icon,
    title,
    description,
    onClick,
  }) {
    return (
      <button className="quick-action" onClick={onClick}>
        <span className="quick-icon">
          <Icon name={icon} size={19} />
        </span>

        <span className="quick-text">
          <strong>{title}</strong>
          <span>{description}</span>
        </span>

        <Icon name="arrow" size={17} />
      </button>
    );
  }

    // =========================================================
  // MAIN APPLICATION LAYOUT
  // =========================================================

  const filteredEvidenceRecords = evidenceRecords.filter((record) => {
    const searchText = evidenceSearch.toLowerCase();

    return (
      String(record.file_name || record.filename || "")
        .toLowerCase()
        .includes(searchText) ||
      String(record.sha256 || record.hash || "")
        .toLowerCase()
        .includes(searchText) ||
      String(record.audit_id || "")
        .toLowerCase()
        .includes(searchText)
    );
  });
  if (showIntro) {
  return <IntroPage onLaunch={() => setShowIntro(false)} />;
}

  return (
    <div className="app-layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <Icon name="shield" size={24} />
          </div>

          <div className="brand-text">
            <strong>VANISH</strong>
            <span>FORENSIC AUDIT</span>
          </div>
        </div>

        <div className="sidebar-section-label">
          MAIN MENU
        </div>

        <nav className="sidebar-navigation">
          {navigation.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${
                activePage === item.name ? "active" : ""
              }`}
              onClick={() => setActivePage(item.name)}
            >
              <Icon name={item.icon} size={19} />
              <span>{item.name}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="backend-status-card">
            <div className="backend-status-heading">
              <span
                className={`status-indicator ${
                  backendStatus === "Connected"
                    ? "online"
                    : backendStatus === "Checking..."
                    ? "checking"
                    : "offline"
                }`}
              />

              <strong>Backend Status</strong>
            </div>

            <span className="backend-status-text">
              {backendStatus}
            </span>

            {backendError && (
              <span className="backend-error-text">
                {backendError}
              </span>
            )}
          </div>

          <div className="sidebar-footer">
            <span>VANISH Digital Forensics</span>
            <span>Prototype v1.0</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main-content">
        {/* TOP BAR */}
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-section">
              VANISH
            </span>

            <span className="topbar-divider">/</span>

            <span className="topbar-current-page">
              {activePage}
            </span>
          </div>

          <div className="topbar-right">
            <div className="system-status">
              <span
                className={`status-indicator ${
                  backendStatus === "Connected"
                    ? "online"
                    : "offline"
                }`}
              />

              <span>{backendStatus}</span>
            </div>

            <button
              className="topbar-icon-button"
              title="Refresh dashboard"
              onClick={() => {
                refreshDashboard();
                loadEvidence();
              }}
            >
              <Icon name="refresh" size={18} />
            </button>
          </div>
        </header>

        {/* PAGE CONTENT */}
        <div className="page-content">
          {/* ================= DASHBOARD ================= */}
          {activePage === "Dashboard" && (
            <>
              <section className="welcome-section">
                <div>
                  <div className="eyebrow">
                    DIGITAL FORENSIC AUDIT FRAMEWORK
                  </div>

                  <h1>Dashboard</h1>

                  <p className="welcome-description">
                    Monitor evidence collection, integrity
                    verification, sanitization assessments,
                    and forensic audit activity.
                  </p>
                </div>
              </section>

              {/* DASHBOARD STATISTICS */}
              <section className="dashboard-stats-grid">
                <StatCard
                  title="Evidence Records"
                  value={evidenceCount}
                  icon="folder"
                  note="Collected evidence"
                />

                <StatCard
                  title="Audit Logs"
                  value={auditLogCount}
                  icon="activity"
                  note="Recorded activity"
                />

                <StatCard
                  title="Custody Events"
                  value={custodyCount}
                  icon="link"
                  note="Chain records"
                />

                <StatCard
                  title="Custody Chain"
                  value={chainStatus}
                  icon="shield"
                  note="Chain verification"
                />
              </section>

              {/* QUICK ACTIONS */}
              <section className="dashboard-main-grid">
                <div className="panel quick-actions-panel">
                  <div className="panel-header">
                    <div>
                      <h2>Quick Actions</h2>

                      <p>
                        Access forensic verification modules
                      </p>
                    </div>
                  </div>

                  <div className="quick-actions-list">
                    <QuickAction
                      icon="folder"
                      title="Manage Evidence"
                      description="Collect and review evidence records"
                      onClick={() => setActivePage("Evidence")}
                    />

                    <QuickAction
                      icon="shield"
                      title="Integrity Verification"
                      description="Verify SHA-256 evidence hashes"
                      onClick={() =>
                        setActivePage("Integrity Verification")
                      }
                    />

                    <QuickAction
                      icon="trash"
                      title="Sanitization Assessment"
                      description="Assess data sanitization evidence"
                      onClick={() =>
                        setActivePage("Sanitization")
                      }
                    />

                    <QuickAction
                      icon="cloud"
                      title="Cloud Verification"
                      description="Assess cloud deletion evidence"
                      onClick={() =>
                        setActivePage("Cloud Verification")
                      }
                    />
                  </div>
                </div>

                {/* RECENT ACTIVITY */}
                <div className="panel recent-activity-panel">
                  <div className="panel-header">
                    <div>
                      <h2>Recent Activity</h2>

                      <p>
                        Latest recorded audit events
                      </p>
                    </div>

                    <button
                      className="secondary-button"
                      onClick={() => setActivePage("Evidence")}
                    >
                      View Evidence
                      <Icon name="arrow" size={15} />
                    </button>
                  </div>

                  {recentActivity.length === 0 ? (
                    <div className="evidence-table-state">
                      <Icon name="activity" size={24} />

                      <h3>No recent activity</h3>

                      <p>
                        Audit events will appear here when
                        activities are recorded.
                      </p>
                    </div>
                  ) : (
                    <div className="recent-activity-list">
                      {recentActivity.map((item, index) => (
                        <div
                          className="recent-activity-item"
                          key={
                            item.id ||
                            item.audit_id ||
                            index
                          }
                        >
                          <div className="activity-icon">
                            <Icon name="activity" size={17} />
                          </div>

                          <div className="activity-content">
                            <strong>
                              {getActivityText(item)}
                            </strong>

                            <span>
                              {getActivityDate(item)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </section>

              {/* SYSTEM STATUS */}
              <section className="panel dashboard-system-panel">
                <div className="panel-header">
                  <div>
                    <h2>System Status</h2>

                    <p>
                      VANISH backend service connectivity
                    </p>
                  </div>
                </div>

                <div className="system-status-row">
                  <div className="system-status-item">
                    <span
                      className={`status-indicator ${
                        backendStatus === "Connected"
                          ? "online"
                          : "offline"
                      }`}
                    />

                    <strong>Backend API</strong>

                    <span>{backendStatus}</span>
                  </div>

                  <div className="system-status-item">
                    <span
                      className={`status-indicator ${
                        chainStatus === "Verified"
                          ? "online"
                          : chainStatus === "Checking..."
                          ? "checking"
                          : "offline"
                      }`}
                    />

                    <strong>Chain of Custody</strong>

                    <span>{chainStatus}</span>
                  </div>
                </div>
              </section>
            </>
          )}

          {/* ================= EVIDENCE ================= */}
          {activePage === "Evidence" && (
            <EvidencePage
              records={filteredEvidenceRecords}
              totalRecords={evidenceRecords.length}
              loading={evidenceLoading}
              error={evidenceError}
              search={evidenceSearch}
              setSearch={setEvidenceSearch}
              scanLoading={scanLoading}
              uploadLoading={uploadLoading}
              selectedFile={selectedFile}
              setSelectedFile={setSelectedFile}
              onScan={handleScan}
              onUpload={handleUpload}
              onRefresh={loadEvidence}
              message={evidenceMessage}
              messageType={evidenceMessageType}
            />
          )}

          {/* ================= INTEGRITY ================= */}
          {activePage === "Integrity Verification" && (
            <IntegrityPage
              records={evidenceRecords}
              selectedAuditId={selectedAuditId}
              setSelectedAuditId={setSelectedAuditId}
              loading={evidenceLoading}
              verifying={integrityLoading}
              error={integrityError}
              result={integrityResult}
              onVerify={handleIntegrityVerification}
              onRefresh={loadEvidence}
            />
          )}

          {/* ================= SANITIZATION ================= */}
          {activePage === "Sanitization" && (
            <SanitizationPage
              records={evidenceRecords}
              loading={evidenceLoading}
              verifying={sanitizationLoading}
              target={sanitizationTarget}
              setTarget={setSanitizationTarget}
              method={sanitizationMethod}
              setMethod={setSanitizationMethod}
              storageType={storageType}
              setStorageType={setStorageType}
              residualMarker={residualMarker}
              setResidualMarker={setResidualMarker}
              error={sanitizationError}
              result={sanitizationResult}
              onVerify={handleSanitizationVerification}
              onRefresh={loadEvidence}
            />
          )}

          {/* ================= CLOUD VERIFICATION ================= */}
          {activePage === "Cloud Verification" && (
            <CloudVerificationPage
              deletionConfirmed={cloudDeletionConfirmed}
              setDeletionConfirmed={setCloudDeletionConfirmed}
              residualObjects={cloudResidualObjects}
              setResidualObjects={setCloudResidualObjects}
              retainedVersions={cloudRetainedVersions}
              setRetainedVersions={setCloudRetainedVersions}
              backupCopies={cloudBackupCopies}
              setBackupCopies={setCloudBackupCopies}
              retentionActive={cloudRetentionActive}
              setRetentionActive={setCloudRetentionActive}
              locationsChecked={cloudLocationsChecked}
              setLocationsChecked={setCloudLocationsChecked}
              evidenceComplete={cloudEvidenceComplete}
              setEvidenceComplete={setCloudEvidenceComplete}
              loading={cloudLoading}
              error={cloudError}
              result={cloudResult}
              onVerify={handleCloudVerification}
            />
          )}
          {/* ================= CHAIN OF CUSTODY ================= */}
          {activePage === "Chain of Custody" && (
            <>
              <section className="welcome-section">
                <div>
                  <div className="eyebrow">
                    FORENSIC EVIDENCE TRACEABILITY
                  </div>

                  <h1>Chain of Custody</h1>

                  <p className="welcome-description">
                    Track the recorded history and handling
                    events associated with digital evidence.
                  </p>
                </div>

                <button
                  className="secondary-button"
                  onClick={loadCustodyData}
                  disabled={custodyLoading}
                >
                  <Icon name="refresh" size={17} />
                  {custodyLoading ? "Refreshing..." : "Refresh"}
                </button>
              </section>

              {/* CUSTODY STATISTICS */}
              <section className="integrity-stats-grid">
                <IntegrityStat
                  label="Custody Events"
                  value={custodyCount}
                  icon="link"
                />

                <IntegrityStat
                  label="Chain Status"
                  value={chainStatus}
                  icon="shield"
                  variant={
                    chainStatus === "Verified"
                      ? "success"
                      : chainStatus === "Failed"
                      ? "danger"
                      : ""
                  }
                />

                <IntegrityStat
                  label="Displayed Events"
                  value={custodyEventsList.length}
                  icon="activity"
                />
              </section>

              {/* AUDIT ID FILTER */}
              <section className="panel evidence-table-panel">
                <div className="panel-header">
                  <div>
                    <h2>Filter Custody Records</h2>
                    <p>
                      Search custody events using an Audit ID.
                    </p>
                  </div>
                </div>

                <div className="evidence-search-wrapper">
                  <Icon name="search" size={18} />

                  <input
                    type="text"
                    placeholder="Enter Audit ID..."
                    value={custodyAuditFilter}
                    onChange={(event) =>
                      setCustodyAuditFilter(event.target.value)
                    }
                  />

                  <button
                    className="primary-button"
                    onClick={loadCustodyData}
                    disabled={custodyLoading}
                  >
                    Search
                  </button>
                </div>

                {custodyAuditFilter && (
                  <button
                    className="secondary-button"
                    style={{ marginTop: "12px" }}
                    onClick={() => {
                      setCustodyAuditFilter("");
                      api.custodyEvents()
                        .then((data) => {
                          const events = getArray(data);

                          setCustodyEventsList(events);
                          setCustodyCount(
                            typeof data?.total === "number"
                              ? data.total
                              : events.length
                          );
                        })
                        .catch((error) => {
                          setCustodyError(error.message);
                        });
                    }}
                  >
                    Clear Filter
                  </button>
                )}
              </section>

              {/* ERRORS */}
              {custodyError && (
                <div className="evidence-message error">
                  {custodyError}
                </div>
              )}

              {/* EVENT RECORDS */}
              <section className="panel evidence-table-panel">
                <div className="panel-header">
                  <div>
                    <h2>Custody Event Records</h2>
                    <p>
                      Recorded evidence handling and audit events
                    </p>
                  </div>
                </div>

                {custodyLoading ? (
                  <div className="evidence-table-state">
                    <div className="loading-indicator" />
                    <p>Loading custody records...</p>
                  </div>
                ) : custodyEventsList.length === 0 ? (
                  <div className="evidence-table-state">
                    <div className="overview-icon">
                      <Icon name="link" size={25} />
                    </div>

                    <h3>No custody events found</h3>

                    <p>
                      No records were returned for the selected
                      Audit ID.
                    </p>
                  </div>
                ) : (
                  <div className="evidence-table-scroll">
                    <table className="evidence-table">
                      <thead>
                        <tr>
                          <th>Timestamp</th>
                          <th>Action</th>
                          <th>Audit ID</th>
                          <th>Evidence ID</th>
                          <th>Actor</th>
                          <th>Previous Hash</th>
                          <th>Event Hash</th>
                        </tr>
                      </thead>

                      <tbody>
                        {custodyEventsList.map((event, index) => (
                          <tr
                            key={
                              event.event_id ||
                              `${event.audit_id}-${index}`
                            }
                          >
                            <td>
                              {formatDate(event.timestamp)}
                            </td>

                            <td>
                              <span className="evidence-status">
                                {event.action ||
                                  event.event_type ||
                                  "Event"}
                              </span>
                            </td>

                            <td>
                              <span
                                className="audit-id-cell"
                                title={event.audit_id || ""}
                              >
                                {event.audit_id
                                  ? `${String(event.audit_id).slice(0, 12)}...`
                                  : "—"}
                              </span>
                            </td>

                            <td>
                              <span
                                className="audit-id-cell"
                                title={event.evidence_id || ""}
                              >
                                {event.evidence_id
                                  ? `${String(event.evidence_id).slice(0, 12)}...`
                                  : "—"}
                              </span>
                            </td>

                            <td>
                              {event.actor || "—"}
                            </td>

                            <td>
                              <span
                                className="audit-id-cell"
                                title={event.previous_hash || ""}
                              >
                                {event.previous_hash
                                  ? `${String(event.previous_hash).slice(0, 12)}...`
                                  : "—"}
                              </span>
                            </td>

                            <td>
                              <span
                                className="audit-id-cell"
                                title={event.event_hash || ""}
                              >
                                {event.event_hash
                                  ? `${String(event.event_hash).slice(0, 12)}...`
                                  : "—"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="evidence-table-footer">
                  Showing {custodyEventsList.length} custody events
                </div>
              </section>

              {/* CHAIN VERIFICATION DETAILS */}
              {custodyVerification && (
                <section className="panel integrity-analysis-panel">
                  <div className="panel-header">
                    <div>
                      <h2>Chain Verification Details</h2>
                      <p>
                        Backend chain integrity verification response
                      </p>
                    </div>
                  </div>

                  <div className="sanitization-result-details">
                    {Object.entries(custodyVerification).map(
                      ([key, value]) => (
                        <div
                          className="sanitization-detail-row"
                          key={key}
                        >
                          <strong>
                            {key.replaceAll("_", " ")}
                          </strong>

                          <span>
                            {typeof value === "object" &&
                            value !== null
                              ? JSON.stringify(value)
                              : String(value ?? "—")}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </section>
              )}
            </>
          )}{/* ================= REPORTS ================= */}
{activePage === "Reports" && (
  <>
    <section className="welcome-section">
      <div>
        <div className="eyebrow">FORENSIC DOCUMENTATION</div>
        <h1>Reports</h1>
        <p className="welcome-description">
          Generate and review forensic audit reports
          using recorded evidence verification results.
        </p>
      </div>
    </section>

    <section className="panel">
      <h2>Generate Forensic Report</h2>
      <p>
        Enter an Audit ID to generate a detailed
        integrity verification report.
      </p>

      <div style={{ marginTop: "20px" }}>
        <label
          style={{
            display: "block",
            marginBottom: "8px",
            fontWeight: "600",
          }}
        >
          Audit ID
        </label>

        <input
          type="text"
          value={reportAuditId}
          onChange={(e) => {
            setReportAuditId(e.target.value);
            setReportError("");
          }}
          placeholder="Enter audit ID"
          style={{
            width: "100%",
            padding: "12px",
            borderRadius: "8px",
            border: "1px solid #444",
            background: "#171525",
            color: "white",
            boxSizing: "border-box",
          }}
        />

        <button
          className="primary-button"
          onClick={generateReport}
          disabled={reportLoading}
          style={{ marginTop: "15px" }}
        >
          <Icon name="file" size={17} />
          {reportLoading
            ? "Generating Report..."
            : "Generate Report"}
        </button>
      </div>

      {reportError && (
        <div style={{ marginTop: "20px", color: "#ff7070" }}>
          <strong>Report Generation Failed</strong>
          <p>{reportError}</p>
        </div>
      )}
    </section>

    {reportResult && (
      <>
        <section className="panel">
          <h2>Report Generation Status</h2>

          <p>
            <strong>Status:</strong>{" "}
            {reportResult.report_status || "Generated"}
          </p>

          <p>
            <strong>Audit ID:</strong>{" "}
            {reportResult.audit_id || reportAuditId}
          </p>

          <p>
            <strong>Report ID:</strong>{" "}
            {reportResult.report?.report_id || "N/A"}
          </p>

          <p>
            <strong>Report Type:</strong>{" "}
            {reportResult.report?.report_type || "N/A"}
          </p>

          <p>
            <strong>Generated At:</strong>{" "}
            {reportResult.report?.generated_at
              ? formatDate(reportResult.report.generated_at)
              : "N/A"}
          </p>

          <p>
            <strong>Report File:</strong>
          </p>

          <div
            style={{
              padding: "12px",
              background: "#171525",
              borderRadius: "8px",
              overflowWrap: "anywhere",
              fontSize: "13px",
            }}
          >
            {reportResult.report_path || "Path unavailable"}
          </div>
        </section>

        {reportResult.report?.summary && (
          <section className="panel">
            <h2>Integrity Summary</h2>

            <div className="stats-grid">
              <div className="stat-card">
                <span>Total Files</span>
                <h3>
                  {reportResult.report.summary.total_files ?? 0}
                </h3>
              </div>

              <div className="stat-card">
                <span>Intact</span>
                <h3>
                  {reportResult.report.summary.intact ?? 0}
                </h3>
              </div>

              <div className="stat-card">
                <span>Modified</span>
                <h3>
                  {reportResult.report.summary.modified ?? 0}
                </h3>
              </div>

              <div className="stat-card">
                <span>Missing</span>
                <h3>
                  {reportResult.report.summary.missing ?? 0}
                </h3>
              </div>

              <div className="stat-card">
                <span>Invalid</span>
                <h3>
                  {reportResult.report.summary.invalid ?? 0}
                </h3>
              </div>
            </div>

            <p style={{ marginTop: "20px" }}>
              <strong>Overall Status:</strong>{" "}
              {reportResult.report.summary.overall_status || "N/A"}
            </p>
          </section>
        )}

        {Array.isArray(reportResult.report?.file_results) &&
          reportResult.report.file_results.length > 0 && (
            <section className="panel">
              <h2>File Verification Results</h2>

              {reportResult.report.file_results.map(
                (file, index) => (
                  <div
                    key={index}
                    style={{
                      padding: "15px",
                      marginBottom: "12px",
                      background: "#171525",
                      borderRadius: "8px",
                    }}
                  >
                    <p>
                      <strong>File:</strong>{" "}
                      {file.file_name || file.file_path}
                    </p>

                    <p>
                      <strong>Status:</strong>{" "}
                      {file.status || "N/A"}
                    </p>

                    <p>
                      <strong>Integrity Verified:</strong>{" "}
                      {file.integrity_verified ? "Yes" : "No"}
                    </p>

                    <p>
                      <strong>Expected SHA-256:</strong>
                    </p>

                    <div
                      style={{
                        fontSize: "12px",
                        overflowWrap: "anywhere",
                      }}
                    >
                      {file.expected_hash || "N/A"}
                    </div>

                    <p>
                      <strong>Actual SHA-256:</strong>
                    </p>

                    <div
                      style={{
                        fontSize: "12px",
                        overflowWrap: "anywhere",
                      }}
                    >
                      {file.actual_hash || "N/A"}
                    </div>
                  </div>
                )
              )}
            </section>
          )}

        {reportResult.report?.forensic_analysis && (
          <section className="panel">
            <h2>Forensic Analysis</h2>

            <p>
              <strong>Analysis Status:</strong>{" "}
              {reportResult.report.forensic_analysis.analysis_status}
            </p>

            <p>
              <strong>Risk Level:</strong>{" "}
              {reportResult.report.forensic_analysis.risk_level}
            </p>

            <p>
              <strong>Risk Score:</strong>{" "}
              {reportResult.report.forensic_analysis.risk_score}
            </p>

            <p>
              {reportResult.report.forensic_analysis.summary}
            </p>

            {Array.isArray(
              reportResult.report.forensic_analysis.findings
            ) &&
              reportResult.report.forensic_analysis.findings.length > 0 && (
                <>
                  <h3>Findings</h3>
                  <ul>
                    {reportResult.report.forensic_analysis.findings.map(
                      (finding, index) => (
                        <li key={index}>
                          {typeof finding === "string"
                            ? finding
                            : JSON.stringify(finding)}
                        </li>
                      )
                    )}
                  </ul>
                </>
              )}

            {Array.isArray(
              reportResult.report.forensic_analysis.recommendations
            ) &&
              reportResult.report.forensic_analysis.recommendations.length > 0 && (
                <>
                  <h3>Recommendations</h3>
                  <ul>
                    {reportResult.report.forensic_analysis.recommendations.map(
                      (recommendation, index) => (
                        <li key={index}>
                          {recommendation}
                        </li>
                      )
                    )}
                  </ul>
                </>
              )}
          </section>
        )}
      </>
    )}
  </>
)}
        </div>
      </main>
    </div>
  );
}
export default App;