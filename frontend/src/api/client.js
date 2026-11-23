const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      Accept: "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = `API error: ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep default error message
    }

    throw new Error(message);
  }

  return response.json();
}

export const api = {
  // System
  health: () => request("/health"),

  // Evidence
  evidence: () => request("/api/v1/evidence"),

  scanEvidence: () =>
    request("/api/v1/evidence/scan", {
      method: "POST",
    }),

  uploadEvidence: (file) => {
    const formData = new FormData();
    formData.append("file", file);

    return request("/api/v1/evidence/upload", {
      method: "POST",
      body: formData,
    });
  },

  // Audit
  auditLogs: () => request("/api/v1/audit/logs"),

  auditRecords: (auditId) =>
    request(`/api/v1/evidence/audit/${auditId}`),

  verifyAudit: (auditId) =>
    request(`/api/v1/evidence/verify/${auditId}`),

  auditReport: (auditId) =>
    request(`/api/v1/evidence/report/${auditId}`),

  // Chain of custody
  custodyEvents: () =>
    request("/api/v1/custody/events"),

  custodyEventsByAudit: (auditId) =>
    request(`/api/v1/custody/events/${auditId}`),

  verifyCustodyChain: () =>
    request("/api/v1/custody/chain/verify"),

  // Sanitization verification
  verifySanitization: ({
    target_path,
    sanitization_method = "unknown",
    storage_type = "filesystem",
    residual_marker = "",
  }) => {
    const params = new URLSearchParams({
      target_path,
      sanitization_method,
      storage_type,
    });

    if (residual_marker) {
      params.append("residual_marker", residual_marker);
    }

    return request(
      `/api/v1/sanitization/verify?${params.toString()}`,
      {
        method: "POST",
      }
    );
  },
    // Cloud verification
  verifyCloudDeletion: (payload) =>
    request("/api/v1/cloud/verify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }),
};
