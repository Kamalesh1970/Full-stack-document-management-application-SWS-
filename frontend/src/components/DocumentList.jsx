import { useState } from 'react';
import { deleteDocument, downloadUrl } from '../api';

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentList({ documents, loading, error, onDeleted }) {
  const [confirmId, setConfirmId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState('');

  async function handleDelete(id) {
    setDeletingId(id);
    setDeleteError('');
    try {
      await deleteDocument(id);
      onDeleted();
    } catch (err) {
      setDeleteError(err.message);
    } finally {
      setDeletingId(null);
      setConfirmId(null);
    }
  }

  return (
    <div className="documents">
      <h2>Documents {documents.length > 0 && <span className="count">{documents.length}</span>}</h2>

      {loading && <p className="hint">Loading...</p>}
      {error && <p className="message error">{error}</p>}
      {deleteError && <p className="message error">{deleteError}</p>}
      {!loading && !error && documents.length === 0 && (
        <p className="hint">No documents yet. Upload one to get started.</p>
      )}

      <ul>
        {documents.map((doc) => (
          <li key={doc._id} className="doc">
            <div className="doc-info">
              <span className="doc-name" title={doc.originalName}>{doc.originalName}</span>
              <span className="doc-meta">
                {formatSize(doc.size)} · {new Date(doc.createdAt).toLocaleString()}
              </span>
            </div>

            <div className="doc-actions">
              {confirmId === doc._id ? (
                <>
                  <span className="confirm-text">Delete?</span>
                  <button
                    className="danger"
                    onClick={() => handleDelete(doc._id)}
                    disabled={deletingId === doc._id}
                  >
                    Yes
                  </button>
                  <button className="ghost" onClick={() => setConfirmId(null)}>No</button>
                </>
              ) : (
                <>
                  <a className="button ghost" href={downloadUrl(doc._id)} download>Download</a>
                  <button className="ghost danger-text" onClick={() => setConfirmId(doc._id)}>Delete</button>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
