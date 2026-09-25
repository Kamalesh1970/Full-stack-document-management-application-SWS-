import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { askQuestion, downloadUrl } from '../api';

export default function ChatPanel({ hasDocuments }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, asking]);

  async function handleSubmit(e) {
    e.preventDefault();
    const text = question.trim();
    if (!text || asking) return;

    setMessages((prev) => [...prev, { role: 'user', text }]);
    setQuestion('');
    setAsking(true);

    try {
      const res = await askQuestion(text);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: res.answer, sources: res.sources, provider: res.provider },
      ]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'error', text: err.message }]);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="chat">
      <h2>Ask a question</h2>

      <div className="messages">
        {messages.length === 0 && (
          <p className="hint">
            {hasDocuments
              ? 'Try something like "How many days of leave do employees get?"'
              : 'Upload a document first, then ask questions about it here.'}
          </p>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`bubble ${msg.role}`}>
            {msg.role === 'assistant' ? <ReactMarkdown>{msg.text}</ReactMarkdown> : <p>{msg.text}</p>}

            {msg.provider === 'mock' && <span className="tag">mock answer</span>}

            {msg.sources?.length > 0 && (
              <div className="sources">
                <span>Sources:</span>
                {msg.sources.map((s) => (
                  <a key={s._id} href={downloadUrl(s._id)} download title="Download">
                    {s.originalName}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}

        {asking && <div className="bubble assistant thinking">Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <form className="ask" onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your documents..."
          maxLength={2000}
        />
        <button type="submit" disabled={asking || !question.trim()}>Send</button>
      </form>
    </div>
  );
}
