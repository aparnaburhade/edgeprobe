import { useState } from "react";

function App() {
  const [promptId, setPromptId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runEvaluation = async () => {
    if (!promptId) return;

    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/runs/execute", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt_id: Number(promptId),
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error running evaluation:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>EdgeProbe</h1>

      <input
        type="number"
        placeholder="Enter prompt ID"
        value={promptId}
        onChange={(e) => setPromptId(e.target.value)}
        style={{ padding: "0.5rem", marginRight: "0.5rem" }}
      />

      <button onClick={runEvaluation} style={{ padding: "0.5rem 1rem" }}>
        {loading ? "Running..." : "Run Evaluation"}
      </button>

      {result && (
        <pre style={{ marginTop: "1rem", whiteSpace: "pre-wrap" }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;