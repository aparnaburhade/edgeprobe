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

// -- Design tokens (Coolors: 080f0f · a4bab7 · f2f5cc · f1ece4 · a52422)
// https://coolors.co/080f0f-a4bab7-f2f5cc-f1ece4-a52422
const INK = "#080f0f";
const SAGE = "#a4bab7";
const LIME = "#f2f5cc";
const PAPER = "#f1ece4";
const BRICK = "#a52422";

const ACCENT = BRICK;
const ACCENT_FOCUS = "#6b8f89";
const GRAY_BG = PAPER;
const GRAY_BORDER = SAGE;
const GRAY_INPUT = "#e8e4db";
const TEXT_DARK = INK;
const TEXT_MID = "#2c3635";
const TEXT_MUTED = "#4a5654";
const TEXT_FAINT = "#5f6d6a";
const WHITE = "#ffffff";
const CREAM = "#faf9f7";
const FONT_DISPLAY = "'Cormorant Garamond', Georgia, serif";
const FONT_UI = "'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif";

// -- Style map --------------------------------------------------
const S = {
  page: {
    minHeight: "100vh",
    background: `linear-gradient(168deg, #faf8f5 0%, ${PAPER} 42%, #e8e2d8 100%)`,
    fontFamily: "inherit",
    textAlign: "left",
    fontSize: "17px",
    color: TEXT_MID,
  },

  nav: {
    position: "sticky",
    top: 0,
    zIndex: 50,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "16px clamp(20px, 4vw, 40px)",
    backgroundColor: "rgba(255,255,255,0.72)",
    backdropFilter: "saturate(140%) blur(16px)",
    WebkitBackdropFilter: "saturate(140%) blur(16px)",
    borderBottom: "1px solid rgba(164,186,183,0.4)",
  },
  navBrand: { display: "flex", flexDirection: "column", gap: "6px" },
  navMark: {
    fontFamily: FONT_DISPLAY,
    fontSize: "clamp(24px, 3.2vw, 32px)",
    fontWeight: 700,
    color: TEXT_DARK,
    letterSpacing: "0.02em",
    margin: 0,
    lineHeight: 1,
  },
  navRule: {
    width: "40px",
    height: "2px",
    backgroundColor: BRICK,
  },
  navAside: {
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.22em",
    textTransform: "uppercase",
    color: TEXT_FAINT,
    textAlign: "right",
    lineHeight: 1.6,
  },

  main: {
    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    padding: 0,
    gap: 0,
  },

  hero: {
    padding: "clamp(28px, 6vw, 56px) clamp(20px, 4vw, 40px) clamp(24px, 4vw, 44px)",
    maxWidth: "940px",
    margin: "0 auto",
    width: "100%",
    boxSizing: "border-box",
  },
  heroEyebrow: {
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.28em",
    textTransform: "uppercase",
    color: TEXT_FAINT,
    margin: "0 0 14px",
  },
  heroTitle: {
    fontFamily: FONT_DISPLAY,
    fontSize: "clamp(44px, 8.5vw, 88px)",
    fontWeight: 700,
    lineHeight: "1.02",
    color: TEXT_DARK,
    margin: "0 0 16px",
    letterSpacing: "-0.035em",
    maxWidth: "14ch",
  },
  heroLead: {
    fontSize: "clamp(17px, 2.1vw, 21px)",
    lineHeight: 1.75,
    color: TEXT_MUTED,
    fontWeight: 400,
    maxWidth: "36em",
    margin: "0 0 20px",
  },
  heroRule: {
    width: "56px",
    height: "1px",
    background: "linear-gradient(90deg, " + SAGE + ", transparent)",
    margin: 0,
  },

  pillars: {
    padding: "0 clamp(20px, 4vw, 40px) clamp(28px, 5vw, 48px)",
    maxWidth: "1080px",
    margin: "0 auto",
    width: "100%",
    boxSizing: "border-box",
  },
  pillarsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: "clamp(12px, 2vw, 20px)",
  },
  pillar: {
    padding: "22px 22px 26px",
    borderTop: "1px solid rgba(164,186,183,0.85)",
    backgroundColor: "rgba(255,255,255,0.5)",
  },
  pillarNum: {
    fontFamily: FONT_DISPLAY,
    fontSize: "48px",
    fontWeight: 700,
    color: "rgba(8,15,15,0.14)",
    margin: "0 0 10px",
    lineHeight: 1,
  },
  pillarTitle: {
    fontFamily: FONT_DISPLAY,
    fontSize: "15px",
    fontWeight: 700,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: TEXT_DARK,
    margin: "0 0 8px",
  },
  pillarText: {
    fontSize: "16px",
    lineHeight: 1.8,
    color: TEXT_MUTED,
    margin: 0,
    fontWeight: 400,
  },

  studio: {
    padding: "clamp(28px, 5vw, 48px) clamp(20px, 4vw, 40px) clamp(36px, 6vw, 64px)",
    maxWidth: "680px",
    margin: "0 auto",
    width: "100%",
    boxSizing: "border-box",
    borderTop: "1px solid rgba(164,186,183,0.45)",
  },
  studioEyebrow: {
    fontSize: "11px",
    fontWeight: 600,
    letterSpacing: "0.28em",
    textTransform: "uppercase",
    color: TEXT_FAINT,
    margin: "0 0 10px",
  },
  studioHeading: {
    fontFamily: FONT_DISPLAY,
    fontSize: "clamp(36px, 5.8vw, 52px)",
    fontWeight: 700,
    color: TEXT_DARK,
    margin: "0 0 10px",
    lineHeight: 1.1,
    letterSpacing: "-0.025em",
  },
  studioIntro: {
    fontSize: "17px",
    lineHeight: 1.75,
    color: TEXT_MUTED,
    margin: "0 0 22px",
    fontWeight: 400,
    maxWidth: "38em",
  },

  card: {
    backgroundColor: "rgba(255,255,255,0.92)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    border: "1px solid rgba(164,186,183,0.55)",
    borderRadius: "2px",
    boxShadow: "0 40px 80px -48px rgba(8,15,15,0.18)",
    padding: "clamp(18px, 3vw, 26px)",
    width: "100%",
    maxWidth: "100%",
  },

  workflowStack: {
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  },
  workflowCard: {
    borderRadius: "2px",
    padding: "18px 18px 20px",
    border: "1px solid rgba(164,186,183,0.45)",
    backgroundColor: "rgba(255,255,255,0.75)",
  },
  workflowCardRun: {
    borderLeft: "4px solid " + BRICK,
    backgroundColor: "rgba(255,255,255,0.88)",
  },
  workflowCardCreate: {
    borderLeft: "4px solid " + SAGE,
    backgroundColor: "rgba(242,245,204,0.28)",
  },
  workflowCardKicker: {
    fontSize: "10px",
    fontWeight: 700,
    letterSpacing: "0.22em",
    textTransform: "uppercase",
    margin: "0 0 6px",
  },
  workflowCardTitle: {
    fontFamily: FONT_DISPLAY,
    fontSize: "clamp(26px, 4.2vw, 34px)",
    fontWeight: 700,
    color: TEXT_DARK,
    margin: "0 0 6px",
    lineHeight: 1.15,
    letterSpacing: "-0.02em",
  },
  workflowCardLead: {
    fontSize: "15px",
    lineHeight: 1.7,
    color: TEXT_MUTED,
    margin: "0 0 14px",
    fontWeight: 450,
    maxWidth: "36em",
  },

  // Input row
  inputRow: { display: "flex", gap: "14px", flexWrap: "wrap", alignItems: "stretch" },
  inputBlock: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginTop: 0,
  },
  inputLabel: {
    fontSize: "16px",
    color: TEXT_MID,
    fontWeight: "800",
    margin: 0,
    letterSpacing: "0.02em",
  },
  inputHelper: {
    fontSize: "15px",
    color: TEXT_FAINT,
    margin: 0,
    lineHeight: "1.65",
  },
  inputExample: {
    fontSize: "15px",
    color: TEXT_FAINT,
    margin: "4px 0 0",
    lineHeight: "1.65",
  },
  demoRow: {
    marginTop: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px",
    flexWrap: "wrap",
  },
  demoHint: {
    fontSize: "15px",
    color: TEXT_FAINT,
    margin: 0,
    lineHeight: "1.65",
  },
  secondaryBtn: {
    border: "1px solid rgba(164,186,183,0.9)",
    backgroundColor: "rgba(255,255,255,0.6)",
    color: TEXT_MID,
    borderRadius: "2px",
    fontSize: "13px",
    fontWeight: "600",
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    padding: "14px 22px",
    minHeight: "48px",
    cursor: "pointer",
    whiteSpace: "nowrap",
    transition: "background-color 0.2s, border-color 0.2s",
  },
  input: {
    flex: "1 1 200px",
    padding: "16px 18px",
    backgroundColor: CREAM,
    border: "1px solid transparent",
    borderRadius: "2px",
    fontSize: "17px",
    color: TEXT_DARK,
    outline: "none",
    transition: "border-color 0.2s, background-color 0.2s",
    fontFamily: "inherit",
    minHeight: "52px",
    boxSizing: "border-box",
  },
  btnBase: {
    padding: "17px 32px",
    backgroundColor: ACCENT,
    color: WHITE,
    border: "none",
    borderRadius: "2px",
    fontSize: "13px",
    fontWeight: "600",
    letterSpacing: "0.18em",
    textTransform: "uppercase",
    cursor: "pointer",
    whiteSpace: "nowrap",
    transition: "background-color 0.2s, opacity 0.2s",
    fontFamily: "inherit",
    minHeight: "52px",
    boxSizing: "border-box",
  },
  btnDisabled: { opacity: 0.55, cursor: "not-allowed" },

  // Error box
  errorBox: {
    backgroundColor: "rgba(165,36,34,0.06)",
    border: "1px solid rgba(165,36,34,0.35)",
    borderRadius: "2px",
    padding: "18px 22px",
    marginTop: "10px",
    fontSize: "15px",
    color: INK,
    lineHeight: "1.65",
    fontWeight: "500",
  },

  // Empty state
  empty: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    marginTop: 0,
    textAlign: "center",
    padding: "clamp(20px, 4vw, 36px) 20px",
  },
  emptyIconBox: {
    width: "72px",
    height: "72px",
    backgroundColor: "rgba(255,255,255,0.5)",
    border: "1px solid rgba(164,186,183,0.5)",
    borderRadius: "2px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "14px",
  },
  emptyHeading: {
    fontFamily: FONT_DISPLAY,
    fontSize: "clamp(28px, 4.2vw, 38px)",
    fontWeight: 700,
    color: TEXT_DARK,
    margin: "0 0 10px",
    lineHeight: 1.15,
  },
  emptySub: {
    fontSize: "17px",
    color: TEXT_MUTED,
    margin: 0,
    maxWidth: "28em",
    lineHeight: 1.75,
    fontWeight: 400,
  },

  resultsShell: {
    padding: "clamp(20px, 4vw, 36px) clamp(20px, 4vw, 40px) clamp(32px, 5vw, 56px)",
    maxWidth: "800px",
    margin: "0 auto",
    width: "100%",
    boxSizing: "border-box",
    borderTop: "1px solid rgba(164,186,183,0.45)",
  },

  // -- Result layout
  resultWrap: {
    marginTop: 0,
    width: "100%",
    maxWidth: "100%",
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },

  // Shared section building blocks
  sectionLabel: {
    fontSize: "11px",
    fontWeight: 700,
    color: TEXT_FAINT,
    textTransform: "uppercase",
    letterSpacing: "0.24em",
    margin: "0 0 8px",
  },
  sectionCard: {
    backgroundColor: "rgba(255,255,255,0.88)",
    border: "1px solid rgba(164,186,183,0.45)",
    borderRadius: "2px",
    boxShadow: "0 24px 48px -32px rgba(8,15,15,0.1)",
    padding: "18px 20px",
  },

  // Response
  responseText: {
    fontSize: "18px",
    color: TEXT_MID,
    lineHeight: "1.85",
    margin: 0,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  placeholderText: {
    fontSize: "17px",
    color: TEXT_FAINT,
    margin: 0,
    lineHeight: "1.7",
    fontStyle: "italic",
  },

  // Score (sans-serif for numerals & evaluation copy — easier to scan than display serif)
  riskRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: "10px",
    marginBottom: "12px",
    paddingBottom: "12px",
    borderBottom: "1px solid rgba(164,186,183,0.45)",
    fontFamily: FONT_UI,
  },
  riskLabel: {
    fontSize: "16px",
    fontWeight: "600",
    color: TEXT_MUTED,
    letterSpacing: "0.04em",
    fontFamily: FONT_UI,
  },
  riskPill: {
    fontSize: "11px",
    fontWeight: "600",
    padding: "8px 16px",
    borderRadius: "2px",
    letterSpacing: "0.16em",
    textTransform: "uppercase",
    fontFamily: FONT_UI,
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "10px",
    fontFamily: FONT_UI,
  },
  statBox: {
    backgroundColor: "rgba(242,245,204,0.45)",
    borderRadius: "2px",
    padding: "14px 12px",
    textAlign: "center",
    border: "1px solid rgba(164,186,183,0.4)",
  },
  statNum: {
    fontFamily: FONT_UI,
    fontSize: "32px",
    fontWeight: "800",
    color: TEXT_DARK,
    lineHeight: "1.1",
    marginBottom: "4px",
    display: "block",
    fontVariantNumeric: "tabular-nums",
  },
  statLabel: {
    fontFamily: FONT_UI,
    fontSize: "13px",
    color: TEXT_MUTED,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  scoreMeterRow: {
    display: "flex",
    alignItems: "baseline",
    gap: "12px",
    flexWrap: "wrap",
    marginBottom: "12px",
    fontFamily: FONT_UI,
  },
  scoreMeterValue: {
    fontFamily: FONT_UI,
    fontSize: "clamp(48px, 8vw, 64px)",
    fontWeight: 800,
    color: TEXT_DARK,
    letterSpacing: "-0.04em",
    lineHeight: 1,
    fontVariantNumeric: "tabular-nums",
  },
  scoreMeterHint: {
    fontFamily: FONT_UI,
    fontSize: "16px",
    color: TEXT_FAINT,
    fontWeight: "500",
    flex: "1 1 220px",
    lineHeight: 1.55,
  },
  summaryPara: {
    fontFamily: FONT_UI,
    margin: "0 0 10px",
    fontSize: "17px",
    color: TEXT_MID,
    lineHeight: 1.75,
    fontWeight: "450",
  },
  failureType: {
    fontFamily: FONT_UI,
    fontSize: "14px",
    color: TEXT_FAINT,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    margin: 0,
  },
  scoreSectionLabel: {
    fontFamily: FONT_UI,
    fontSize: "11px",
    fontWeight: 700,
    color: TEXT_FAINT,
    textTransform: "uppercase",
    letterSpacing: "0.24em",
    margin: "0 0 8px",
  },
  selectControl: {
    width: "100%",
    padding: "16px 18px",
    backgroundColor: CREAM,
    border: "1px solid transparent",
    borderRadius: "2px",
    fontSize: "17px",
    color: TEXT_DARK,
    fontFamily: "inherit",
    cursor: "pointer",
    minHeight: "52px",
    boxSizing: "border-box",
  },
  genSection: {
    marginTop: 0,
    paddingTop: 0,
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
    gap: "10px",
    fontSize: "16px",
    color: TEXT_MID,
    fontWeight: "500",
    cursor: "pointer",
    userSelect: "none",
    padding: "6px 0",
  },
  genActions: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    flexWrap: "wrap",
    marginTop: "6px",
  },
  genOk: {
    fontSize: "17px",
    color: "#2a4d42",
    margin: 0,
    lineHeight: 1.6,
    fontWeight: "600",
  },
  inlineField: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  smallLabel: {
    fontSize: "15px",
    color: TEXT_MID,
    fontWeight: "800",
    margin: 0,
    letterSpacing: "0.03em",
  },
  countInput: {
    width: "88px",
    padding: "14px 12px",
    backgroundColor: CREAM,
    border: "1px solid transparent",
    borderRadius: "2px",
    fontSize: "18px",
    color: TEXT_DARK,
    fontFamily: "inherit",
    minHeight: "52px",
    boxSizing: "border-box",
  },

  // Claims
  claimsList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  claimCard: {
    border: "1px solid rgba(164,186,183,0.5)",
    borderRadius: "2px",
    padding: "14px 16px",
    backgroundColor: "rgba(255,255,255,0.75)",
  },
  claimTopRow: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "14px",
    marginBottom: "6px",
  },
  claimText: {
    fontSize: "17px",
    fontWeight: "500",
    color: TEXT_DARK,
    lineHeight: "1.65",
    margin: 0,
    flex: 1,
  },
  evidenceWrap: {
    marginTop: "6px",
    paddingTop: "8px",
    borderTop: "1px dashed rgba(164,186,183,0.6)",
  },
  evidenceLabel: {
    fontSize: "12px",
    fontWeight: "800",
    color: TEXT_FAINT,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: "6px",
  },
  evidenceText: {
    fontSize: "16px",
    color: TEXT_MUTED,
    lineHeight: "1.65",
    margin: 0,
    fontStyle: "italic",
  },
  confRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginTop: "8px",
  },
  confBarTrack: {
    flex: 1,
    height: "8px",
    backgroundColor: GRAY_INPUT,
    borderRadius: "4px",
    overflow: "hidden",
  },
  confLabel: {
    fontSize: "15px",
    color: TEXT_FAINT,
    fontWeight: "700",
    minWidth: "44px",
    textAlign: "right",
  },

  footer: {
    padding: "20px clamp(20px, 4vw, 40px) 28px",
    borderTop: "1px solid rgba(164,186,183,0.35)",
    textAlign: "center",
  },
  footerText: {
    fontSize: "11px",
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    color: TEXT_FAINT,
    fontWeight: 500,
    margin: 0,
  },
};

// -- Verdict colours --------------------------------------------
const VERDICT_STYLE = {
  supported:    { color: "#1e3d36", bg: LIME, border: SAGE },
  unsupported:  { color: "#6b4a1e", bg: "#f5edd8", border: "#c4a574" },
  contradicted: { color: BRICK, bg: "#fceae9", border: BRICK },
  unverifiable: { color: TEXT_MUTED, bg: PAPER, border: SAGE },
};
const RISK_PILL = {
  low:    { color: "#1e3d36", bg: LIME },
  medium: { color: "#6b4a1e", bg: "#f5edd8" },
  high:   { color: BRICK, bg: "#fceae9" },
};

// -- VerdictBadge -----------------------------------------------
function VerdictBadge({ verdict = "unverifiable" }) {
  const key = verdict.toLowerCase();
  const vs  = VERDICT_STYLE[key] ?? VERDICT_STYLE.unverifiable;
  return (
    <span style={{
      fontSize: "11px",
      fontWeight: "600",
      padding: "8px 14px",
      borderRadius: "2px",
      whiteSpace: "nowrap",
      border: '1px solid ' + vs.border,
      letterSpacing: "0.14em",
      backgroundColor: vs.bg,
      color: vs.color,
      textTransform: "uppercase",
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
    <div style={{ fontFamily: FONT_UI }}>
      <p style={S.scoreSectionLabel}>Evaluation Score</p>
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
        <div style={{ ...S.statsGrid, marginTop: score.summary ? "8px" : 0 }}>
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
            borderRadius: "4px",
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
        <span style={{ color: TEXT_FAINT, fontWeight: "500", fontSize: "17px", textTransform: "none", letterSpacing: "0.02em" }}>
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
      <header style={S.nav}>
        <div style={S.navBrand}>
          <p style={S.navMark}>Edge Probe</p>
          <div style={S.navRule} aria-hidden />
        </div>
        <p style={S.navAside}>
          Claim-level
          <br />
          evaluation
        </p>
      </header>

      <main style={S.main}>
        <section style={S.hero}>
          <p style={S.heroEyebrow}>Hallucination intelligence</p>
          <h1 style={S.heroTitle}>
            Clarity for every{" "}
            <span style={{ fontStyle: "italic", fontWeight: 700, color: BRICK }}>model</span> answer.
          </h1>
          <p style={S.heroLead}>
            Decompose AI output into verifiable claims, ground them in reference text, and
            see where confidence meets fact—without treating a whole paragraph as a single
            guess.
          </p>
          <div style={S.heroRule} aria-hidden />
        </section>

        <section style={S.pillars}>
          <div style={S.pillarsGrid}>
            <article style={S.pillar}>
              <p style={S.pillarNum}>01</p>
              <h2 style={S.pillarTitle}>Decompose</h2>
              <p style={S.pillarText}>
                Responses become discrete claims you can scan, question, and trace—rather than
                one opaque block of prose.
              </p>
            </article>
            <article style={S.pillar}>
              <p style={S.pillarNum}>02</p>
              <h2 style={S.pillarTitle}>Ground</h2>
              <p style={S.pillarText}>
                Each claim is read against the prompt&apos;s reference context so support is
                explicit, not assumed.
              </p>
            </article>
            <article style={S.pillar}>
              <p style={S.pillarNum}>03</p>
              <h2 style={S.pillarTitle}>Judge</h2>
              <p style={S.pillarText}>
                Verdicts, a distilled risk readout, and a plain-language summary complete the
                picture.
              </p>
            </article>
          </div>
        </section>

        <section style={S.studio}>
          <p style={S.studioEyebrow}>The studio</p>
          <h2 style={S.studioHeading}>Run an analysis</h2>
          <p style={S.studioIntro}>
            Two paths: run the model on something already in your library, or author new
            edge-case prompts first—each has its own panel below.
          </p>

          <div style={S.card}>
          <div style={S.workflowStack}>
            <div style={{ ...S.workflowCard, ...S.workflowCardRun }}>
              <p style={{ ...S.workflowCardKicker, color: BRICK }}>Run the model</p>
              <h3 style={S.workflowCardTitle}>Use a saved prompt</h3>
              <p style={S.workflowCardLead}>
                Choose a row from your database or type a numeric ID, then analyze. This is the
                path for anything you have already stored.
              </p>
              <div style={S.inputBlock}>
            <p style={S.inputLabel}>Saved prompts</p>
            <select
              style={S.selectControl}
              value={selectValue}
              disabled={listLoading}
              onChange={(e) => {
                const v = e.target.value;
                setPromptId(v);
                setError(null);
              }}
              onFocus={(e) => (e.target.style.borderColor = ACCENT_FOCUS)}
              onBlur={(e) => (e.target.style.borderColor = "transparent")}
            >
              <option value="">— Select a prompt —</option>
              {prompts.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} · {p.domain}/{p.category} — {p.prompt_preview}
                </option>
              ))}
            </select>

            <p style={{ ...S.inputLabel, marginTop: "10px" }}>Prompt ID</p>
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
                onFocus={(e) => (e.target.style.borderColor = ACCENT_FOCUS)}
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
              </div>
            </div>

            <div style={{ ...S.workflowCard, ...S.workflowCardCreate }}>
              <p style={{ ...S.workflowCardKicker, color: "#3d524e" }}>Grow the library</p>
              <h3 style={S.workflowCardTitle}>Generate new prompts</h3>
              <p style={S.workflowCardLead}>
                Sample adversarial templates by domain and category, then save them to the
                database. New IDs appear in the list above when you are done.
              </p>
              <div style={S.genSection}>
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
                          style={{ width: "22px", height: "22px", cursor: genLoading ? "not-allowed" : "pointer", flexShrink: 0 }}
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
                    style={{ ...S.secondaryBtn, padding: "14px 22px" }}
                  >
                    {genLoading ? "Generating…" : "Generate & save"}
                  </button>
                </div>
              </div>
              {genNotice && (
                <p style={genNotice.ok ? S.genOk : { ...S.genOk, color: INK }}>
                  {genNotice.text}
                </p>
              )}
              </div>
            </div>
          </div>
          </div>
        </section>

        <section style={S.resultsShell}>
          {result ? (
            <div style={S.resultWrap}>
              <p style={S.studioEyebrow}>Results</p>
              <h2 style={{ ...S.studioHeading, marginBottom: "4px" }}>Your last run</h2>
              <PromptSection   promptText={result.prompt_text} />
              <ResponseSection text={result.response_text} />
              <ScoreSection    score={result.score} />
              <ClaimsSection   claims={result.claims} />
            </div>
          ) : (
            <div style={S.empty}>
              <div style={S.emptyIconBox}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                    stroke={TEXT_FAINT} strokeWidth="1.25" strokeLinejoin="round"
                  />
                  <polyline points="14 2 14 8 20 8"
                    stroke={TEXT_FAINT} strokeWidth="1.25" strokeLinejoin="round" />
                  <line x1="8" y1="13" x2="16" y2="13"
                    stroke={TEXT_FAINT} strokeWidth="1.25" strokeLinecap="round" />
                  <line x1="8" y1="17" x2="12" y2="17"
                    stroke={TEXT_FAINT} strokeWidth="1.25" strokeLinecap="round" />
                </svg>
              </div>
              <h3 style={S.emptyHeading}>Awaiting your first run</h3>
              <p style={S.emptySub}>
                Choose or create a prompt above, then analyze. A structured readout will appear
                here—prompt, model reply, score, and every claim annotated.
              </p>
            </div>
          )}
        </section>
      </main>

      <footer style={S.footer}>
        <p style={S.footerText}>Edge Probe — claim-level AI reliability checks</p>
      </footer>
    </div>
  );
}

export default App;
