import { useEffect, useState } from "react";
import "./App.css";

const STORAGE_KEY = "silosense_chat_messages";
const TRACE_STORAGE_KEY = "silosense_selected_trace";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTrace, setSelectedTrace] = useState(null);

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

  const clearChat = () => {
    localStorage.clear();
    location.reload();
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
      }
    }, 10);
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

    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    const data = await res.json();

    streamAssistantMessage(data.reply, data);

    setMessage("");
  };

  return (
    <div className="app">
      <div className="main-layout">
        <div className="chat-card">
          <div className="header">
            <h1>SiloSense</h1>
            <button onClick={clearChat}>Clear</button>
          </div>

          <div className="messages-container">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`message ${m.role}`}
                onClick={() => m.trace && setSelectedTrace(m.trace)}
              >
                <b>{m.role === "user" ? "You" : m.agent}</b>
                <p>{m.text}</p>
                {m.source && <small>{m.source}</small>}
              </div>
            ))}
          </div>

          <div className="input-row">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>

        <div className="trace-panel">
          <h2>Trace</h2>

          {selectedTrace && (
            <>
              <p><b>Query:</b> {selectedTrace.query}</p>
              <p><b>Mode:</b> {selectedTrace.mode}</p>

              {selectedTrace.agent_outputs?.map((a, i) => (
                <div key={i}>
                  <h4>{a.agent}</h4>
                  <p>{a.reply}</p>

                  {a.retrieval?.map((r, j) => (
                    <div key={j}>
                      <small>{r.source} | score: {r.score}</small>
                      <p>{r.chunk}</p>
                    </div>
                  ))}
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;