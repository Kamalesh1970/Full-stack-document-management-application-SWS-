import { useEffect, useState } from 'react';
import { getDocuments } from './api';
import UploadForm from './components/UploadForm';
import DocumentList from './components/DocumentList';
import ChatPanel from './components/ChatPanel';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadDocuments() {
    try {
      setDocuments(await getDocuments());
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h1>Document Assistant</h1>
        <p>Upload your documents and ask questions about them.</p>
      </header>

      <main className="layout">
        <section className="panel">
          <UploadForm onUploaded={loadDocuments} />
          <DocumentList
            documents={documents}
            loading={loading}
            error={error}
            onDeleted={loadDocuments}
          />
        </section>

        <section className="panel chat-panel">
          <ChatPanel hasDocuments={documents.length > 0} />
        </section>
      </main>
    </div>
  );
}
