import { useCallback, useEffect, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

const DOMAINS = ["general", "healthcare", "coding"];
const CATEGORIES = [
  "ambiguity",
  "misleading_context",
  "near_fact",
  "insufficient_info",
  "multi_hop",
];

// -- Design tokens ----------------------------------------------
const PURPLE      = "#7c3aed";
const GRAY_BG     = "#f4f5f7";
const GRAY_BORDER = "#e8e8ed";
const GRAY_INPUT  = "#f3f4f6";
const TEXT_DARK   = "#111827";
const TEXT_MID    = "#374151";
const TEXT_MUTED  = "#6b7280";
const TEXT_FAINT  = "#9ca3af";
const WHITE       = "#ffffff";

// -- Style map --------------------------------------------------
const S = {
  page: {
    minHeight: "100vh",
    backgroundColor: GRAY_BG,
    fontFamily: "'Plus Jakarta Sans', 'Segoe UI', system-ui, -apple-system, sans-serif",
    textAlign: "left",
  },

  // Header
  header: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    padding: "20px 32px",
    backgroundColor: WHITE,
    borderBottom: '1px solid ' + GRAY_BORDER,
  },
  headerIcon: {
    width: "38px",
    height: "38px",
    backgroundColor: PURPLE,
    borderRadius: "10px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  headerTitleBlock: { display: "flex", flexDirection: "column", gap: "2px" },
  headerTitle: {
    fontSize: "32px",
    fontWeight: "800",
    color: TEXT_DARK,
    margin: 0,
    lineHeight: "1.1",
    letterSpacing: "-0.8px",
  },
  headerSub: {
    fontSize: "14px",
    color: TEXT_MUTED,
    margin: "0",
    letterSpacing: "0.1px",
    fontWeight: "500",
  },

  // Main layout
  main: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "64px 24px 84px",
    gap: "24px",
  },

  // Intro / guide
  introWrap: {
    width: "100%",
    maxWidth: "620px",
    display: "flex",
    flexDirection: "column",
    gap: "18px",
  },
  infoCard: {
    backgroundColor: WHITE,
    borderRadius: "14px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)",
    padding: "22px 24px",
  },
  infoTitle: {
    margin: "0 0 10px",
    fontSize: "17px",
    fontWeight: "650",
    color: TEXT_DARK,
    letterSpacing: "-0.2px",
  },
  infoText: {
    margin: 0,
    fontSize: "14px",
    color: TEXT_MUTED,
    lineHeight: "1.8",
    fontWeight: "450",
  },
  stepsList: {
    margin: 0,
    paddingLeft: "18px",
    color: TEXT_MID,
    fontSize: "14px",
    lineHeight: "1.9",
  },
  stepItem: {
    marginBottom: "4px",
  },

  // Analyze card
  card: {
    backgroundColor: WHITE,
    borderRadius: "16px",
    boxShadow: "0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)",
    padding: "36px 40px",
    width: "100%",
    maxWidth: "620px",
  },
  cardTitle: {
    fontSize: "24px",
    fontWeight: "700",
    color: TEXT_DARK,
    margin: "0 0 8px",
    letterSpacing: "-0.5px",
  },
  cardSub: {
    fontSize: "14px",
    color: TEXT_MUTED,
    margin: "0 0 26px",
    lineHeight: "1.75",
    fontWeight: "450",
  },

  // Input row
  inputRow: { display: "flex", gap: "10px" },
  inputBlock: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginTop: "2px",
  },
  inputLabel: {
    fontSize: "13px",
    color: TEXT_MID,
    fontWeight: "650",
    margin: 0,
  },
  inputHelper: {
    fontSize: "12.5px",
    color: TEXT_FAINT,
    margin: 0,
    lineHeight: "1.65",
  },
  inputExample: {
    fontSize: "12.5px",
    color: TEXT_FAINT,
    margin: "2px 0 0",
    lineHeight: "1.65",
  },
  demoRow: {
    marginTop: "10px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "10px",
    flexWrap: "wrap",
  },
  demoHint: {
    fontSize: "12.5px",
    color: TEXT_FAINT,
    margin: 0,
    lineHeight: "1.65",
  },
  secondaryBtn: {
    border: '1px solid ' + GRAY_BORDER,
    backgroundColor: WHITE,
    color: TEXT_MID,
    borderRadius: "9px",
    fontSize: "12px",
    fontWeight: "600",
    padding: "8px 12px",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  input: {
    flex: 1,
    padding: "11px 14px",
    backgroundColor: GRAY_INPUT,
    border: "1.5px solid transparent",
    borderRadius: "10px",
    fontSize: "14px",
    color: TEXT_DARK,
    outline: "none",
    transition: "border-color 0.15s",
    fontFamily: "inherit",
  },
  btnBase: {
    padding: "11px 22px",
    backgroundColor: PURPLE,
    color: WHITE,
    border: "none",
    borderRadius: "10px",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
    whiteSpace: "nowrap",
    transition: "background-color 0.15s, opacity 0.15s",
    fontFamily: "inherit",
    letterSpacing: "0.1px",
  },
  btnDisabled: { opacity: 0.55, cursor: "not-allowed" },

  // Error box
  errorBox: {
    backgroundColor: "#fef2f2",
    border: "1px solid #fca5a5",
    borderRadius: "10px",
    padding: "12px 16px",
    marginTop: "10px",
    fontSize: "13px",
    color: "#b91c1c",
    lineHeight: "1.65",
    fontWeight: "500",
  },

  // Demo tip box
  demoTipBox: {
    backgroundColor: "#f0f9ff",
    border: "1px solid #bfdbfe",
    borderRadius: "10px",
    padding: "14px 16px",
    marginTop: "14px",
    fontSize: "12.5px",
    color: "#0369a1",
    lineHeight: "1.7",
  },
  demoTipTitle: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#0369a1",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    margin: "0 0 6px",
  },

  // Empty state
  empty: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    marginTop: "60px",
    textAlign: "center",
  },
  emptyIconBox: {
    width: "60px",
    height: "60px",
    backgroundColor: WHITE,
    border: '1px solid ' + GRAY_BORDER,
    borderRadius: "14px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "18px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
  },
  emptyHeading: {
    fontSize: "18px",
    fontWeight: "650",
    color: TEXT_MID,
    margin: "0 0 8px",
  },
  emptySub: {
    fontSize: "14px",
    color: TEXT_FAINT,
    margin: 0,
    maxWidth: "380px",
    lineHeight: "1.75",
  },

  // -- Result layout
  resultWrap: {
    marginTop: "12px",
    width: "100%",
    maxWidth: "660px",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },

  // Shared section building blocks
  sectionLabel: {
    fontSize: "11px",
    fontWeight: "650",
    color: TEXT_MUTED,
    textTransform: "uppercase",
    letterSpacing: "0.9px",
    margin: "0 0 12px",
  },
  sectionCard: {
    backgroundColor: WHITE,
    borderRadius: "14px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)",
    padding: "24px 28px",
  },

  // Response
  responseText: {
    fontSize: "15px",
    color: TEXT_MID,
    lineHeight: "1.9",
    margin: 0,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  placeholderText: {
    fontSize: "13px",
    color: TEXT_FAINT,
    margin: 0,
    lineHeight: "1.7",
    fontStyle: "italic",
  },

  // Score
  riskRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "18px",
    paddingBottom: "16px",
    borderBottom: '1px solid ' + GRAY_BORDER,
  },
  riskLabel: { fontSize: "13px", fontWeight: "600", color: TEXT_MUTED },
  riskPill: {
    fontSize: "13px",
    fontWeight: "700",
    padding: "6px 18px",
    borderRadius: "20px",
    letterSpacing: "0.5px",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "10px",
  },
  statBox: {
    backgroundColor: GRAY_BG,
    borderRadius: "10px",
    padding: "14px 10px",
    textAlign: "center",
  },
  statNum: {
    fontSize: "24px",
    fontWeight: "700",
    color: TEXT_DARK,
    lineHeight: "1.1",
    marginBottom: "5px",
    display: "block",
  },
  statLabel: {
    fontSize: "10.5px",
    color: TEXT_MUTED,
    fontWeight: "500",
    textTransform: "uppercase",
    letterSpacing: "0.4px",
  },
  scoreMeterRow: {
    display: "flex",
    alignItems: "baseline",
    gap: "12px",
    marginBottom: "14px",
  },
  scoreMeterValue: {
    fontSize: "36px",
    fontWeight: "800",
    color: TEXT_DARK,
    letterSpacing: "-1px",
    lineHeight: 1,
  },
  scoreMeterHint: {
    fontSize: "12px",
    color: TEXT_FAINT,
    fontWeight: "500",
    flex: 1,
  },
  summaryPara: {
    margin: "0 0 12px",
    fontSize: "13.5px",
    color: TEXT_MID,
    lineHeight: 1.75,
    fontWeight: "450",
  },
  failureType: {
    fontSize: "11px",
    color: TEXT_FAINT,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: "0.4px",
    margin: 0,
  },
  selectControl: {
    width: "100%",
    padding: "10px 12px",
    backgroundColor: GRAY_INPUT,
    border: "1.5px solid transparent",
    borderRadius: "10px",
    fontSize: "13px",
    color: TEXT_DARK,
    fontFamily: "inherit",
    cursor: "pointer",
  },
  genSection: {
    marginTop: "22px",
    paddingTop: "22px",
    borderTop: "1px solid " + GRAY_BORDER,
  },
  genTitle: {
    fontSize: "14px",
    fontWeight: "650",
    color: TEXT_DARK,
    margin: "0 0 12px",
  },
  genGrid: {
    display: "grid",
    gap: "12px",
  },
  catGrid: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
  },
  catChip: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "12px",
    color: TEXT_MID,
    fontWeight: "500",
    cursor: "pointer",
    userSelect: "none",
  },
  genActions: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexWrap: "wrap",
    marginTop: "4px",
  },
  genOk: {
    fontSize: "12.5px",
    color: "#047857",
    margin: 0,
    lineHeight: 1.6,
  },
  inlineField: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  smallLabel: {
    fontSize: "12px",
    color: TEXT_MID,
    fontWeight: "600",
    margin: 0,
  },
  countInput: {
    width: "72px",
    padding: "8px 10px",
    backgroundColor: GRAY_INPUT,
    border: "1.5px solid transparent",
    borderRadius: "8px",
    fontSize: "14px",
    color: TEXT_DARK,
    fontFamily: "inherit",
  },

  // Claims
  claimsList: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  claimCard: {
    border: '1px solid ' + GRAY_BORDER,
    borderRadius: "10px",
    padding: "14px 16px",
    backgroundColor: "#fafafa",
  },
  claimTopRow: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "12px",
    marginBottom: "8px",
  },
  claimText: {
    fontSize: "14.5px",
    fontWeight: "500",
    color: TEXT_DARK,
    lineHeight: "1.6",
    margin: 0,
    flex: 1,
  },
  evidenceWrap: {
    marginTop: "4px",
    paddingTop: "8px",
    borderTop: '1px dashed ' + GRAY_BORDER,
  },
  evidenceLabel: {
    fontSize: "10px",
    fontWeight: "700",
    color: TEXT_FAINT,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "3px",
  },
  evidenceText: {
    fontSize: "12.5px",
    color: TEXT_MUTED,
    lineHeight: "1.6",
    margin: 0,
    fontStyle: "italic",
  },
  confRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginTop: "10px",
  },
  confBarTrack: {
    flex: 1,
    height: "4px",
    backgroundColor: GRAY_BORDER,
    borderRadius: "2px",
    overflow: "hidden",
  },
  confLabel: {
    fontSize: "11px",
    color: TEXT_FAINT,
    fontWeight: "600",
    minWidth: "34px",
    textAlign: "right",
  },
};

// -- Verdict colours --------------------------------------------
const VERDICT_STYLE = {
  supported:    { color: "#059669", bg: "#ecfdf5", border: "#6ee7b7" },
  unsupported:  { color: "#d97706", bg: "#fffbeb", border: "#fcd34d" },
  contradicted: { color: "#dc2626", bg: "#fef2f2", border: "#fca5a5" },
  unverifiable: { color: "#6b7280", bg: "#f3f4f6", border: "#d1d5db" },
};
const RISK_PILL = {
  low:    { color: "#059669", bg: "#ecfdf5" },
  medium: { color: "#d97706", bg: "#fffbeb" },
  high:   { color: "#dc2626", bg: "#fef2f2" },
};

// -- VerdictBadge -----------------------------------------------
function VerdictBadge({ verdict = "unverifiable" }) {
  const key = verdict.toLowerCase();
  const vs  = VERDICT_STYLE[key] ?? VERDICT_STYLE.unverifiable;
  return (
    <span style={{
      fontSize: "11px",
      fontWeight: "700",
      padding: "3px 10px",
      borderRadius: "20px",
      whiteSpace: "nowrap",
      border: '1px solid ' + vs.border,
      backgroundColor: vs.bg,
      color: vs.color,
      textTransform: "uppercase",
      letterSpacing: "0.4px",
      flexShrink: 0,
    }}>
      {key}
    </span>
  );
}

// -- PromptSection ----------------------------------------------
function PromptSection({ promptText }) {
  const hasPrompt = typeof promptText === "string" && promptText.trim().length > 0;
  return (
    <div>
      <p style={S.sectionLabel}>Prompt</p>
      <div style={S.sectionCard}>
        {hasPrompt ? (
          <p style={S.responseText}>{promptText}</p>
        ) : (
          <p style={S.placeholderText}>
            Prompt text is not available for this run yet.
          </p>
        )}
      </div>
    </div>
  );
}

// -- ResponseSection --------------------------------------------
function ResponseSection({ text }) {
  if (!text) return null;
  return (
    <div>
      <p style={S.sectionLabel}>AI Response</p>
      <div style={S.sectionCard}>
        <p style={S.responseText}>{text}</p>
      </div>
    </div>
  );
}

// -- ScoreSection -----------------------------------------------
function ScoreSection({ score }) {
  if (!score) return null;
  const risk = (score.risk ?? "low").toLowerCase();
  const rp   = RISK_PILL[risk] ?? RISK_PILL.low;
  const hs   = score.hallucination_score;
  const stats = [
    { num: score.supported    ?? 0, label: "Supported"    },
    { num: score.unsupported  ?? 0, label: "Unsupported"  },
    { num: score.contradicted ?? 0, label: "Contradicted" },
    { num: score.unverifiable ?? 0, label: "Unverifiable" },
  ];
  return (
    <div>
      <p style={S.sectionLabel}>Evaluation Score</p>
      <div style={S.sectionCard}>
        {typeof hs === "number" && (
          <div style={S.scoreMeterRow}>
            <span style={S.scoreMeterValue}>{hs}</span>
            <span style={S.scoreMeterHint}>
              Hallucination index (0 = best, 100 = worst). Based on claim verdicts vs reference text.
            </span>
          </div>
        )}
        <div style={S.riskRow}>
          <span style={S.riskLabel}>Overall Risk</span>
          <span style={{ ...S.riskPill, color: rp.color, backgroundColor: rp.bg }}>
            {risk.toUpperCase()} RISK
          </span>
        </div>
        {score.summary && <p style={S.summaryPara}>{score.summary}</p>}
        {score.failure_type && score.failure_type !== "none" && (
          <p style={S.failureType}>Failure mode: {String(score.failure_type).replace(/_/g, " ")}</p>
        )}
        <div style={{ ...S.statsGrid, marginTop: score.summary ? "14px" : 0 }}>
          {stats.map(({ num, label }) => (
            <div key={label} style={S.statBox}>
              <span style={S.statNum}>{num}</span>
              <span style={S.statLabel}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// -- ClaimsSection ----------------------------------------------
function ClaimCard({ claim }) {
  const pct = Math.round((claim.confidence ?? 0) * 100);
  const key = (claim.verdict ?? "unverifiable").toLowerCase();
  const vs  = VERDICT_STYLE[key] ?? VERDICT_STYLE.unverifiable;
  return (
    <div style={S.claimCard}>
      <div style={S.claimTopRow}>
        <p style={S.claimText}>{claim.claim_text}</p>
        <VerdictBadge verdict={claim.verdict} />
      </div>
      {claim.evidence_text && (
        <div style={S.evidenceWrap}>
          <p style={S.evidenceLabel}>Evidence</p>
          <p style={S.evidenceText}>&ldquo;{claim.evidence_text}&rdquo;</p>
        </div>
      )}
      <div style={S.confRow}>
        <div style={S.confBarTrack}>
          <div style={{
            height: "100%",
            width: pct + "%",
            backgroundColor: vs.color,
            borderRadius: "2px",
            transition: "width 0.4s ease",
          }} />
        </div>
        <span style={S.confLabel}>{pct}%</span>
      </div>
    </div>
  );
}

function ClaimsSection({ claims }) {
  if (!claims?.length) return null;
  return (
    <div>
      <p style={S.sectionLabel}>
        Claims Analysis
        <span style={{ color: TEXT_FAINT, fontWeight: "400", textTransform: "none", letterSpacing: 0 }}>
          {" "}— {claims.length} claim{claims.length !== 1 ? "s" : ""}
        </span>
      </p>
      <div style={S.sectionCard}>
        <div style={S.claimsList}>
          {claims.map((claim, i) => (
            <ClaimCard key={`${claim.claim_text ?? ""}-${i}`} claim={claim} />
          ))}
        </div>
      </div>
    </div>
  );
}

// -- App --------------------------------------------------------
function App() {
  const [promptId, setPromptId] = useState("");
  const [prompts, setPrompts]   = useState([]);
  const [listLoading, setListLoading] = useState(false);
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const [genDomain, setGenDomain] = useState("general");
  const [genCats, setGenCats]     = useState(() => [...CATEGORIES]);
  const [genCount, setGenCount]   = useState(3);
  const [genLoading, setGenLoading] = useState(false);
  const [genNotice, setGenNotice]   = useState(null);

  const loadPrompts = useCallback(async () => {
    setListLoading(true);
    try {
      const res = await fetch(`${API_BASE}/prompts/`);
      if (!res.ok) throw new Error(`List failed: ${res.status}`);
      const data = await res.json();
      setPrompts(Array.isArray(data.prompts) ? data.prompts : []);
    } catch (e) {
      console.error(e);
      setPrompts([]);
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPrompts();
  }, [loadPrompts]);

  const sanitizeError = (raw) => {
    if (!raw) return "Something went wrong. Please try again.";
    const lower = String(raw).toLowerCase();
    if (lower.includes("not found") || lower.includes("no prompt") || lower.includes("404"))
      return "No prompt found for this ID. Try a valid prompt ID.";
    if (lower.includes("503") || lower.includes("service unavailable") || lower.includes("openai_api_key"))
      return "The model is unavailable. Check OPENAI_API_KEY on the server and try again.";
    if (lower.includes("502") || lower.includes("bad gateway") || lower.includes("llm service"))
      return "The AI provider returned an error. Try again in a moment.";
    if (lower.includes("network") || lower.includes("fetch") || lower.includes("failed to fetch"))
      return "Cannot reach the backend. Check VITE_API_BASE_URL or that the API is running.";
    if (lower.includes("500") || lower.includes("internal server"))
      return "The server encountered an error. Please try again.";
    return "Something went wrong. Please check the prompt ID and try again.";
  };

  const runEvaluation = async () => {
    if (!promptId.trim()) {
      setError("Please enter a prompt ID.");
      return;
    }
    const pid = Math.floor(Number(promptId));
    if (!Number.isFinite(pid) || pid < 1) {
      setError("Enter a positive integer prompt ID.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/runs/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt_id: pid }),
      });

      const data = await response.json();

      if (!response.ok) {
        const raw = data?.detail || ("Error: " + response.status);
        setError(sanitizeError(typeof raw === "string" ? raw : JSON.stringify(raw)));
        console.error("API error:", raw);
        return;
      }

      setResult(data);
      setError(null);
    } catch (err) {
      setError(sanitizeError(err.message));
      console.error("Error running evaluation:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleGenCat = (c) => {
    setGenCats((prev) => {
      if (prev.includes(c)) {
        if (prev.length <= 1) return prev;
        return prev.filter((x) => x !== c);
      }
      return [...prev, c];
    });
  };

  const runGenerate = async () => {
    setGenNotice(null);
    const n = Math.min(100, Math.max(1, Math.floor(Number(genCount)) || 1));
    setGenCount(n);
    setGenLoading(true);
    try {
      const res = await fetch(`${API_BASE}/prompts/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: genDomain,
          categories: genCats,
          count: n,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        const raw = data?.detail ?? res.statusText;
        setGenNotice({ ok: false, text: typeof raw === "string" ? raw : JSON.stringify(raw) });
        return;
      }
      const created = data.prompts ?? [];
      const ids = created.map((p) => p.id).filter((id) => id != null);
      await loadPrompts();
      if (ids.length) {
        setPromptId(String(ids[0]));
        setGenNotice({
          ok: true,
          text:
            ids.length === 1
              ? `Saved prompt #${ids[0]}. You can run analysis now.`
              : `Saved prompts #${ids.join(", #")}. First ID selected.`,
        });
      } else {
        setGenNotice({ ok: true, text: "Prompts saved. Refresh the list if needed." });
      }
    } catch (e) {
      setGenNotice({ ok: false, text: e.message || "Generate request failed." });
    } finally {
      setGenLoading(false);
    }
  };

  const idNum = Math.floor(Number(promptId));
  const idValid = Number.isFinite(idNum) && idNum >= 1;
  const isDisabled = loading || !promptId.trim() || !idValid;
  const selectValue = prompts.some((p) => String(p.id) === promptId.trim()) ? promptId.trim() : "";

  return (
    <div style={S.page}>

      {/* -- Header --------------------------------- */}
      <header style={S.header}>
        <div style={S.headerIcon}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="#fff" strokeWidth="2" />
            <path d="m16.5 16.5 4 4" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
            <path d="M8 11h6M11 8v6" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
        <div style={S.headerTitleBlock}>
          <p style={S.headerTitle}>Edge Probe</p>
          <p style={S.headerSub}>AI Hallucination Detection</p>
        </div>
      </header>

      {/* -- Main ----------------------------------- */}
      <main style={S.main}>

        {/* Tool explanation */}
        <div style={S.introWrap}>
          <div style={S.infoCard}>
            <p style={S.infoTitle}>What this tool does</p>
            <p style={S.infoText}>
              Edge Probe evaluates AI-generated responses by breaking them into claims and comparing those claims against known reference context to detect possible hallucinations.
            </p>
          </div>
          <div style={S.infoCard}>
            <p style={S.infoTitle}>How it works</p>
            <ol style={S.stepsList}>
              <li style={S.stepItem}>Pick a saved prompt (or generate new edge-case prompts)</li>
              <li style={S.stepItem}>Run analysis: the model answers, then claims are extracted</li>
              <li style={S.stepItem}>Each claim is checked against the prompt&apos;s reference context</li>
              <li style={S.stepItem}>Review the score, summary, and per-claim verdicts</li>
            </ol>
          </div>
        </div>

        {/* Analyze card */}
        <div style={S.card}>
          <h2 style={S.cardTitle}>Analyze AI Response</h2>
          <p style={S.cardSub}>
            Choose a prompt from your database, or generate new ones below. Then run analysis to score the model answer against reference context.
          </p>
          <div style={S.inputBlock}>
            <p style={S.inputLabel}>Saved prompts</p>
            <p style={S.inputHelper}>
              Loaded from the API ({listLoading ? "refreshing…" : `${prompts.length} in list`}).
            </p>
            <select
              style={S.selectControl}
              value={selectValue}
              disabled={listLoading}
              onChange={(e) => {
                const v = e.target.value;
                setPromptId(v);
                setError(null);
              }}
              onFocus={(e) => (e.target.style.borderColor = PURPLE)}
              onBlur={(e) => (e.target.style.borderColor = "transparent")}
            >
              <option value="">— Select a prompt —</option>
              {prompts.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} · {p.domain}/{p.category} — {p.prompt_preview}
                </option>
              ))}
            </select>

            <p style={{ ...S.inputLabel, marginTop: "16px" }}>Prompt ID</p>
            <p style={S.inputExample}>Or type an ID manually</p>
            <div style={S.inputRow}>
              <input
                type="number"
                min={1}
                placeholder="e.g. 5"
                value={promptId}
                onChange={(e) => { setPromptId(e.target.value); setError(null); }}
                onKeyDown={(e) => e.key === "Enter" && !isDisabled && runEvaluation()}
                style={S.input}
                onFocus={(e) => (e.target.style.borderColor = PURPLE)}
                onBlur={(e)  => (e.target.style.borderColor = "transparent")}
              />
              <button
                onClick={runEvaluation}
                disabled={isDisabled}
                style={{ ...S.btnBase, ...(isDisabled ? S.btnDisabled : {}) }}
              >
                {loading ? "Analyzing..." : "Analyze"}
              </button>
            </div>

            {error && (
              <div style={S.errorBox}>
                {error}
              </div>
            )}

            <div style={S.demoRow}>
              <button
                type="button"
                style={S.secondaryBtn}
                onClick={loadPrompts}
                disabled={listLoading}
              >
                Refresh list
              </button>
            </div>

            <div style={S.genSection}>
              <p style={S.genTitle}>Generate edge-case prompts</p>
              <div style={S.genGrid}>
                <div style={S.inlineField}>
                  <p style={S.smallLabel}>Domain</p>
                  <select
                    style={S.selectControl}
                    value={genDomain}
                    disabled={genLoading}
                    onChange={(e) => setGenDomain(e.target.value)}
                  >
                    {DOMAINS.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
                <div style={S.inlineField}>
                  <p style={S.smallLabel}>Categories (at least one)</p>
                  <div style={S.catGrid}>
                    {CATEGORIES.map((c) => (
                      <label key={c} style={S.catChip}>
                        <input
                          type="checkbox"
                          checked={genCats.includes(c)}
                          onChange={() => toggleGenCat(c)}
                          disabled={genLoading}
                        />
                        {c.replace(/_/g, " ")}
                      </label>
                    ))}
                  </div>
                </div>
                <div style={{ ...S.inlineField, flexDirection: "row", alignItems: "flex-end", gap: "12px" }}>
                  <div>
                    <p style={S.smallLabel}>Count</p>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={genCount}
                      onChange={(e) => setGenCount(e.target.value)}
                      disabled={genLoading}
                      style={S.countInput}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={runGenerate}
                    disabled={genLoading || genCats.length === 0}
                    style={{ ...S.secondaryBtn, padding: "10px 16px", fontSize: "13px" }}
                  >
                    {genLoading ? "Generating…" : "Generate & save"}
                  </button>
                </div>
              </div>
              {genNotice && (
                <p style={genNotice.ok ? S.genOk : { ...S.genOk, color: "#b91c1c" }}>
                  {genNotice.text}
                </p>
              )}
            </div>

            <div style={S.demoTipBox}>
              <p style={S.demoTipTitle}>Configuration</p>
              <p style={{ margin: 0, lineHeight: "1.7" }}>
                Point the UI at your API with{" "}
                <code style={{ fontSize: "12px" }}>VITE_API_BASE_URL</code> (defaults to{" "}
                <code style={{ fontSize: "12px" }}>http://127.0.0.1:8000</code>).
              </p>
            </div>
          </div>
        </div>

        {/* Results -- or -- empty state */}
        {result ? (
          <div style={S.resultWrap}>
            <PromptSection   promptText={result.prompt_text} />
            <ResponseSection text={result.response_text} />
            <ScoreSection    score={result.score} />
            <ClaimsSection   claims={result.claims} />
          </div>
        ) : (
          <div style={S.empty}>
            <div style={S.emptyIconBox}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path
                  d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                  stroke={TEXT_FAINT} strokeWidth="1.5" strokeLinejoin="round"
                />
                <polyline points="14 2 14 8 20 8"
                  stroke={TEXT_FAINT} strokeWidth="1.5" strokeLinejoin="round" />
                <line x1="8" y1="13" x2="16" y2="13"
                  stroke={TEXT_FAINT} strokeWidth="1.5" strokeLinecap="round" />
                <line x1="8" y1="17" x2="12" y2="17"
                  stroke={TEXT_FAINT} strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
            <h3 style={S.emptyHeading}>Enter a prompt ID to begin analysis</h3>
            <p style={S.emptySub}>
              Edge Probe will scan for potential AI hallucinations and provide detailed scores
            </p>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;
