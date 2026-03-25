/**
 * client.js
 * ---------
 * Lightweight API client for the EdgeProbe backend.
 *
 * Base URL is read from the environment variable VITE_API_BASE_URL (Vite /
 * React) or REACT_APP_API_BASE_URL (CRA), falling back to the local dev
 * server so the file works out-of-the-box without any configuration.
 *
 * All functions return a parsed JSON object on success.
 * On a non-2xx response they throw an ApiError with the status code and
 * the backend's detail message included.
 */

const BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  (typeof process !== "undefined" && process.env?.REACT_APP_API_BASE_URL) ||
  "http://127.0.0.1:8000";

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

/**
 * Thrown when the backend returns a non-2xx HTTP status.
 *
 * @property {number} status  - HTTP status code
 * @property {string} detail  - Error message from the backend (if available)
 */
export class ApiError extends Error {
  /**
   * @param {number} status
   * @param {string} detail
   */
  constructor(status, detail) {
    super(`API error ${status}: ${detail}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// ---------------------------------------------------------------------------
// Internal helper
// ---------------------------------------------------------------------------

/**
 * POST *path* with a JSON body and return the parsed response.
 *
 * @param {string} path     - Path relative to BASE_URL, e.g. "/api/v1/generate"
 * @param {object} body     - Request payload (will be JSON-serialised)
 * @returns {Promise<any>}  - Parsed JSON response body
 * @throws {ApiError}       - On non-2xx responses
 * @throws {Error}          - On network failures
 */
async function post(path, body) {
  const url = `${BASE_URL}${path}`;

  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
    });
  } catch (networkError) {
    throw new Error(
      `Network request to "${url}" failed: ${networkError.message}`
    );
  }

  // Parse the body regardless of status so we can surface the backend detail.
  let data;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail =
      data?.detail ??
      data?.message ??
      response.statusText ??
      "Unknown error";
    throw new ApiError(response.status, detail);
  }

  return data;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Generate adversarial edge-case prompts.
 *
 * @param {{ domain: string, categories: string[], count: number }} data
 * @returns {Promise<{ prompts: object[] }>}
 *
 * @example
 * const { prompts } = await generatePrompts({
 *   domain: "healthcare",
 *   categories: ["ambiguity", "multi_hop"],
 *   count: 5,
 * });
 */
export async function generatePrompts(data) {
  return post("/api/v1/generate", data);
}

/**
 * Execute an LLM run against a stored prompt.
 *
 * @param {{ prompt_id: number, model_name?: string }} data
 * @returns {Promise<{ prompt_id: number, model_name: string, prompt_text: string, response_text: string }>}
 *
 * @example
 * const result = await executeRun({ prompt_id: 2, model_name: "gpt-4o-mini" });
 */
export async function executeRun(data) {
  return post("/api/v1/execute", data);
}

/**
 * Run end-to-end hallucination evaluation for a completed LLM run.
 *
 * @param {{ run_id: number }} data
 * @returns {Promise<{ run_id: number, prompt_text: string, claims: object[], evaluation: object }>}
 *
 * @example
 * const { claims, evaluation } = await runEvaluation({ run_id: 1 });
 */
export async function runEvaluation(data) {
  return post("/api/v1/evaluations/run", data);
}
