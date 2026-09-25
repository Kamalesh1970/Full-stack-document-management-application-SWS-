import { useRef, useState } from 'react';
import { uploadDocument } from '../api';

const ACCEPTED = '.txt,.md,.json';

export default function UploadForm({ onUploaded }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setMessage({ type: 'error', text: 'Choose a file first' });
      return;
    }

    setUploading(true);
    setMessage(null);
    try {
      const doc = await uploadDocument(file);
      setMessage({ type: 'success', text: `Uploaded ${doc.originalName}` });
      setFile(null);
      inputRef.current.value = '';
      onUploaded();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setUploading(false);
    }
  }

  return (
    <form className="upload" onSubmit={handleSubmit}>
      <h2>Upload</h2>
      <p className="hint">Supported: .txt, .md, .json (max 5 MB)</p>
      <div className="upload-row">
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
        <button type="submit" disabled={uploading}>
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>
      {message && <p className={`message ${message.type}`}>{message.text}</p>}
    </form>
  );
}
