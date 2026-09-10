const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "https://medguard-backend.vercel.app"
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, { code = "UNKNOWN", status = 0 } = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, options);
  } catch {
    throw new ApiError(
      "Could not reach MedGuard's server. Check your connection and try again.",
      { code: "NETWORK" }
    );
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    // FastAPI nests the team's shared error envelope under `detail`.
    const envelope = body?.detail ?? body ?? {};
    let message;
    if (Array.isArray(envelope)) {
      message = envelope.map((err) => err.msg || err.message).filter(Boolean).join(", ");
    } else if (envelope.code === "GEMINI_QUOTA_EXCEEDED") {
      message = "The AI reading service has reached today's request limit. Please try again later, or use the medicine picker below.";
    } else {
      message = envelope.message || "MedGuard's server could not complete this check.";
    }
    throw new ApiError(message, {
      code: Array.isArray(envelope) ? "VALIDATION_ERROR" : (envelope.code || "HTTP_ERROR"),
      status: response.status,
    });
  }

  return body;
}

/** Photos in, full report out: vision, normalisation, interactions, duplicates, alternatives. */
export function runPipeline(files, conditions = [], medicineName = "", medicineNames = []) {
  const form = new FormData();
  files.forEach((file) => form.append("images", file));
  form.append("conditions", JSON.stringify(conditions));
  if (medicineName) form.append("medicine_name", medicineName);
  if (medicineNames.length > 0) form.append("medicine_names", JSON.stringify(medicineNames));
  return request("/pipeline", { method: "POST", body: form });
}

/** Interactions plus duplicate-active-ingredient check for already-known medicines. */
export function checkMedications(medications) {
  return request("/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ medications }),
  });
}

/** Same-ingredient substitutes available in the Egyptian catalogue. */
export function findAlternatives(brandName, dosageMg) {
  return request("/alternatives", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brand_name: brandName, dosage_mg: dosageMg ?? null }),
  });
}

export { BASE_URL };
