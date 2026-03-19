import { useEffect, useState } from "react";
import "./App.css";

const STORAGE_KEY = "silosense_chat_messages";
const TRACE_STORAGE_KEY = "silosense_selected_trace";
const API_BASE_URL = "http://127.0.0.1:8000";

const ROLE_OPTIONS = [
  { value: "employee", label: "Employee" },
  { value: "manager", label: "Manager" },
  { value: "admin", label: "Admin" },
  { value: "engineering_lead", label: "Engineering Lead" },
];

const WORKSPACE_OPTIONS = [
  { value: "all", label: "All Departments" },
  { value: "hr", label: "HR" },
  { value: "engineering", label: "Engineering" },
  { value: "product", label: "Product/Operations" },
];

const safePct = (value, total) => {
  if (!total || total <= 0) return 0;
  return Math.round((value / total) * 100);
};

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [role, setRole] = useState("employee");
  const [workspace, setWorkspace] = useState("all");
  const [domain, setDomain] = useState("hr");
  const [selectedFile, setSelectedFile] = useState(null);
  const [files, setFiles] = useState([]);
  const [kbStatus, setKbStatus] = useState("");
  const [kbStatusType, setKbStatusType] = useState("info");
  const [uploading, setUploading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [activeInsightsTab, setActiveInsightsTab] = useState("trace");
  const [expandedCitations, setExpandedCitations] = useState({});
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    const savedTrace = localStorage.getItem(TRACE_STORAGE_KEY);

    if (saved) setMessages(JSON.parse(saved));
    else {
      setMessages([
        {
          role: "assistant",
          text: "Hi, I'm SiloSense.",
          agent: "System",
          source: "",
          trace: null,
        },
      ]);
    }

    if (savedTrace) setSelectedTrace(JSON.parse(savedTrace));
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(TRACE_STORAGE_KEY, JSON.stringify(selectedTrace));
  }, [selectedTrace]);

  useEffect(() => {
    fetchFiles(domain);
  }, [domain]);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const clearChat = () => {
    localStorage.clear();
    location.reload();
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/analytics`);
      if (!res.ok) throw new Error("Unable to load analytics");
      const data = await res.json();
      setAnalytics(data);
    } catch (error) {
      setAnalytics(null);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchFiles = async (targetDomain) => {
    try {
      const res = await fetch(`${API_BASE_URL}/files?domain=${targetDomain}`);
      if (!res.ok) throw new Error("Unable to fetch files");

      const data = await res.json();
      setFiles(data.files || []);
    } catch (error) {
      setKbStatus("Failed to load files.");
      setKbStatusType("error");
    }
  };

  const uploadFile = async () => {
    if (!selectedFile) {
      setKbStatus("Choose a file before uploading.");
      setKbStatusType("error");
      return;
    }

    setUploading(true);
    setKbStatus("Uploading file...");
    setKbStatusType("info");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API_BASE_URL}/upload?domain=${domain}`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMessage = data?.detail || data?.error || "Upload failed";
        throw new Error(errorMessage);
      }

      setKbStatus(data.message || "Upload successful.");
      setKbStatusType("success");
      setSelectedFile(null);
      await fetchFiles(domain);
    } catch (error) {
      setKbStatus(error.message || "Upload failed.");
      setKbStatusType("error");
    } finally {
      setUploading(false);
    }
  };

  const reindexDomain = async () => {
    setReindexing(true);
    setKbStatus("Reindexing documents...");
    setKbStatusType("info");

    try {
      const res = await fetch(`${API_BASE_URL}/reindex?domain=${domain}`, {
        method: "POST",
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMessage = data?.detail || data?.error || "Reindex failed";
        throw new Error(errorMessage);
      }

      setKbStatus(data.message || "Reindex completed.");
      setKbStatusType("success");
      await fetchFiles(domain);
    } catch (error) {
      setKbStatus(error.message || "Reindex failed.");
      setKbStatusType("error");
    } finally {
      setReindexing(false);
    }
  };

  const streamAssistantMessage = (text, meta) => {
    let index = 0;

    const newMsg = {
      role: "assistant",
      text: "",
      agent: meta.agent,
      source: meta.source,
      trace: meta.trace,
    };

    setMessages((prev) => [...prev, newMsg]);

    const interval = setInterval(() => {
      index++;
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].text = text.slice(0, index);
        return updated;
      });

      if (index >= text.length) {
        clearInterval(interval);
        setSelectedTrace(meta.trace);
        setLoading(false);
        fetchAnalytics();
      }
    }, 10);
  };

  const toggleCitations = (key) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const exportTraceAsJson = () => {
    if (!selectedTrace) return;

    const payload = {
      exported_at: new Date().toISOString(),
      role,
      workspace,
      trace: selectedTrace,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `silosense-trace-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const exportTraceAsMarkdown = () => {
    if (!selectedTrace) return;

    const timelineLines = (selectedTrace.timeline || [])
      .map((event, i) => `${i + 1}. ${event.step} - ${event.details || event.status || ""}`)
      .join("\n");

    const subqueryLines = Object.entries(selectedTrace.subqueries || {})
      .map(([agent, subquery]) => `- **${agent}:** ${subquery}`)
      .join("\n");

    const agentOutputs = (selectedTrace.agent_outputs || [])
      .map((item) => {
        const citations = (item.retrieval || [])
          .map((r, idx) => `  - Citation ${idx + 1}: ${r.source || "Unknown"}${r.score !== undefined ? ` (score: ${r.score})` : ""}${r.chunk ? `\n    ${r.chunk}` : ""}`)
          .join("\n");

        return `### ${item.agent}\n\n${item.reply}\n\n${citations || "- No citations"}`;
      })
      .join("\n\n");

    const markdown = [
      "# SiloSense Trace Report",
      "",
      `- Exported At: ${new Date().toISOString()}`,
      `- Mode: ${selectedTrace.mode || "N/A"}`,
      `- Role: ${selectedTrace.role || role}`,
      `- Workspace: ${selectedTrace.workspace || workspace}`,
      "",
      "## Query",
      "",
      selectedTrace.query || "N/A",
      "",
      "## Timeline",
      "",
      timelineLines || "No timeline events",
      "",
      "## Sub-Queries",
      "",
      subqueryLines || "No sub-queries",
      "",
      "## Agent Outputs",
      "",
      agentOutputs || "No agent outputs",
    ].join("\n");

    const blob = new Blob([markdown], { type: "text/markdown" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `silosense-trace-${Date.now()}.md`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMsg = { role: "user", text: message };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const history = messages.map((m) => ({
      role: m.role,
      text: m.text,
    }));

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history, role, workspace }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.detail || "Failed to send message");
      }

      streamAssistantMessage(data.reply, data);
      setMessage("");
    } catch (error) {
      setLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: error.message || "Something went wrong.",
          agent: "System",
          source: "Client",
          trace: null,
        },
      ]);
    }
  };

  return (
    <div className="app">
      <div className="main-layout">
        <div className="chat-card">
          <div className="header">
            <div>
              <h1>SiloSense</h1>
              <p className="subtitle">Enterprise Multi-Agent Knowledge Assistant</p>
            </div>

            <div className="header-controls">
              <div className="selector-group">
                <label htmlFor="role-select">Role</label>
                <select id="role-select" value={role} onChange={(e) => setRole(e.target.value)}>
                  {ROLE_OPTIONS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="selector-group">
                <label htmlFor="workspace-select">Workspace</label>
                <select id="workspace-select" value={workspace} onChange={(e) => setWorkspace(e.target.value)}>
                  {WORKSPACE_OPTIONS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>

              <button className="clear-btn" onClick={clearChat}>Clear</button>
            </div>
          </div>

          <div className="messages-container">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`message ${m.role}`}
                onClick={() => m.trace && setSelectedTrace(m.trace)}
              >
                <b>{m.role === "user" ? "You" : m.agent}</b>
                <p className="message-text">{m.text}</p>
                {m.source && <small>{m.source}</small>}
              </div>
            ))}
            {loading && <p className="loading-text">Orchestrating agents...</p>}
          </div>

          <div className="input-row">
            <input
              placeholder="Ask across HR, Engineering, and Product context"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage} disabled={loading}>Send</button>
          </div>
        </div>

        <div className="right-column">
          <div className="kb-panel">
            <h2>Knowledge Base Manager</h2>

            <div className="kb-controls">
              <label htmlFor="domain-select">Domain</label>
              <select
                id="domain-select"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
              >
                <option value="hr">HR</option>
                <option value="tech">Tech</option>
              </select>

              <input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />

              <div className="kb-actions">
                <button
                  className="secondary-btn"
                  onClick={uploadFile}
                  disabled={uploading || !selectedFile}
                >
                  {uploading ? "Uploading..." : "Upload"}
                </button>

                <button
                  className="secondary-btn"
                  onClick={reindexDomain}
                  disabled={reindexing}
                >
                  {reindexing ? "Reindexing..." : "Reindex"}
                </button>
              </div>

              {kbStatus && <p className={`kb-status ${kbStatusType}`}>{kbStatus}</p>}

              <div className="file-list-box">
                <h3>Indexed Files ({files.length})</h3>
                {files.length === 0 ? (
                  <p className="empty-state">No files found for this domain.</p>
                ) : (
                  <ul>
                    {files.map((fileName) => (
                      <li key={fileName}>{fileName}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>

          <div className="trace-panel">
            <div className="insights-header">
              <h2>Insights</h2>
              <div className="insights-tabs">
                <button
                  className={activeInsightsTab === "trace" ? "tab-btn active" : "tab-btn"}
                  onClick={() => setActiveInsightsTab("trace")}
                >
                  Trace
                </button>
                <button
                  className={activeInsightsTab === "analytics" ? "tab-btn active" : "tab-btn"}
                  onClick={() => {
                    setActiveInsightsTab("analytics");
                    fetchAnalytics();
                  }}
                >
                  Analytics
                </button>
              </div>
            </div>

            {activeInsightsTab === "trace" && (
              <>
                {!selectedTrace && <p className="empty-state">Select a response in chat to inspect trace.</p>}

                {selectedTrace && (
                  <div className="trace-content">
                    <p><b>Query:</b> {selectedTrace.query}</p>

                    <div className="trace-export-row">
                      <button className="secondary-btn" onClick={exportTraceAsJson}>Export JSON</button>
                      <button className="secondary-btn" onClick={exportTraceAsMarkdown}>Export Markdown</button>
                    </div>

                    <div className="trace-meta-row">
                      <span className="meta-pill">Mode: {selectedTrace.mode}</span>
                      <span className="meta-pill">Role: {selectedTrace.role}</span>
                      <span className="meta-pill">Workspace: {selectedTrace.workspace}</span>
                    </div>

                    <div className="trace-section">
                      <h3>Timeline</h3>
                      <ol className="timeline-list">
                        {(selectedTrace.timeline || []).map((event, i) => (
                          <li key={`${event.step}-${i}`} className="timeline-item">
                            <div className="timeline-step">{event.step}</div>
                            <div className="timeline-details">{event.details || event.status}</div>
                          </li>
                        ))}
                      </ol>
                    </div>

                    <div className="trace-section">
                      <h3>Sub-Queries</h3>
                      {Object.entries(selectedTrace.subqueries || {}).length === 0 && (
                        <p className="empty-state">No decomposition used for this request.</p>
                      )}
                      <div className="subquery-grid">
                        {Object.entries(selectedTrace.subqueries || {}).map(([agent, subquery]) => (
                          <div key={agent} className="subquery-card">
                            <b>{agent}</b>
                            <p>{subquery}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="trace-section">
                      <h3>Agent Outputs</h3>
                      {(selectedTrace.agent_outputs || []).map((item, index) => {
                        const key = `${item.agent}-${index}`;
                        const isOpen = !!expandedCitations[key];
                        return (
                          <div key={key} className="agent-output-card">
                            <p><b>{item.agent}</b></p>
                            <p className="agent-output-reply">{item.reply}</p>

                            <button className="secondary-btn" onClick={() => toggleCitations(key)}>
                              {isOpen ? "Hide Citations" : "Show Citations"}
                            </button>

                            {isOpen && (
                              <div className="retrieval-box">
                                {(item.retrieval || []).length === 0 && (
                                  <p className="empty-state">No retrieval diagnostics available.</p>
                                )}
                                {(item.retrieval || []).map((citation, rIndex) => (
                                  <div key={`${key}-r-${rIndex}`} className="retrieval-item">
                                    <small>
                                      {citation.source || "Unknown"}
                                      {citation.score !== undefined ? ` | score: ${citation.score}` : ""}
                                    </small>
                                    {citation.chunk && <p className="retrieval-chunk">{citation.chunk}</p>}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}

            {activeInsightsTab === "analytics" && (
              <div>
                {analyticsLoading && <p className="empty-state">Loading analytics...</p>}

                {!analyticsLoading && !analytics && (
                  <p className="empty-state">Analytics are unavailable right now.</p>
                )}

                {!analyticsLoading && analytics && (
                  <>
                    <div className="analytics-grid">
                      <div className="analytics-card">
                        <h4>Total Queries</h4>
                        <p>{analytics.total_queries}</p>
                      </div>
                      <div className="analytics-card">
                        <h4>Most Used Agent</h4>
                        <p>{analytics.most_used_agent}</p>
                      </div>
                      <div className="analytics-card">
                        <h4>Most Common Query Type</h4>
                        <p>{analytics.most_common_query_type}</p>
                      </div>
                      <div className="analytics-card">
                        <h4>Avg Response Time</h4>
                        <p>{analytics.average_response_time_ms} ms</p>
                      </div>
                      <div className="analytics-card">
                        <h4>Multi-Agent Queries</h4>
                        <p>{analytics.multi_agent_queries}</p>
                      </div>
                      <div className="analytics-card">
                        <h4>Single-Agent Queries</h4>
                        <p>{analytics.single_agent_queries}</p>
                      </div>
                    </div>

                    <div className="analytics-visuals">
                      <div className="chart-card">
                        <h4>Agent Usage</h4>
                        {Object.entries(analytics.agent_usage || {}).map(([agentName, count]) => {
                          const maxValue = Math.max(...Object.values(analytics.agent_usage || { x: 1 }), 1);
                          const width = safePct(count, maxValue);

                          return (
                            <div key={agentName} className="bar-row">
                              <div className="bar-label">
                                <span>{agentName}</span>
                                <span>{count}</span>
                              </div>
                              <div className="bar-track">
                                <div className="bar-fill" style={{ width: `${width}%` }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      <div className="chart-card">
                        <h4>Single vs Multi Agent</h4>
                        <div className="donut-wrap">
                          <div
                            className="donut-chart"
                            style={{
                              background: `conic-gradient(#0f766e 0 ${safePct(analytics.multi_agent_queries || 0, (analytics.multi_agent_queries || 0) + (analytics.single_agent_queries || 0))}%, #60a5fa ${safePct(analytics.multi_agent_queries || 0, (analytics.multi_agent_queries || 0) + (analytics.single_agent_queries || 0))}% 100%)`,
                            }}
                          >
                            <div className="donut-inner">
                              {safePct(analytics.multi_agent_queries || 0, (analytics.multi_agent_queries || 0) + (analytics.single_agent_queries || 0))}%
                            </div>
                          </div>
                          <div className="donut-legend">
                            <p><span className="legend-dot multi" /> Multi-Agent: {analytics.multi_agent_queries}</p>
                            <p><span className="legend-dot single" /> Single-Agent: {analytics.single_agent_queries}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;