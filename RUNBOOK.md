# Runbook: Document Assistant

Step-by-step guide to set up and run the project locally, check that it works, and fix common problems.

```
Browser (React, :5173) ──► FastAPI backend (:8000) ──► MongoDB (metadata + extracted text)
                                   │               └──► backend/data/uploads/ (the files)
                                   └──► OpenRouter LLM (or mock answers if no key)
```

---

## 1. Prerequisites

| Tool | Version | Check with |
|---|---|---|
| Python | 3.10 or newer | `python3 --version` |
| Node.js + npm | 20 or newer | `node -v` |
| Git | any | `git --version` |
| MongoDB | local install **or** a free Atlas cluster | see step 2 |
| OpenRouter API key | optional (without it, chat gives mock answers) | see step 3 |

---

## 2. Set up MongoDB (pick one)

### Option A: MongoDB Atlas (cloud, nothing to install)

1. Sign up at https://www.mongodb.com/atlas and create a **free (M0) cluster**.
2. **Database Access** → add a database user with a username and password.
3. **Network Access** → add your IP address (or `0.0.0.0/0` for testing only).
4. **Connect** → **Drivers** → copy the connection string. It looks like:
   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/
   ```
5. Replace `<password>` with the real password. You'll paste this into `MONGODB_URI` in step 5.

### Option B: Local MongoDB on Ubuntu 24.04

```bash
sudo apt-get install -y gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod      # start automatically on boot
```

Check that it's running:

```bash
systemctl status mongod           # should say "active (running)"
```

Connection string for local MongoDB: `mongodb://localhost:27017`

### Option C: Local MongoDB on macOS / Windows

- **macOS:** `brew tap mongodb/brew && brew install mongodb-community@8.0 && brew services start mongodb-community@8.0`
- **Windows:** download the MSI from https://www.mongodb.com/try/download/community and install it "as a Service".

Connection string: `mongodb://localhost:27017`

---

## 3. Get an OpenRouter API key (optional)

1. Sign in at https://openrouter.ai
2. Go to **Keys** → **Create Key** and copy it.

The default model `openrouter/free` costs nothing. Skip this step to run with mock answers.

---

## 4. Get the code

```bash
cd document-assistant
```

---

## 5. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

```env
# Required: MongoDB connection (local or Atlas string from step 2)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=document_assistant

# For real AI answers. Leave empty to use mock answers
LLM_API_KEY=your-openrouter-key
LLM_API_BASE=https://openrouter.ai/api/v1
LLM_MODEL=openrouter/free

# Optional
DATA_DIR=data
MAX_FILE_SIZE_MB=5
CORS_ORIGINS=*
```

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

You should see `Application startup complete.` If it stops with
`Could not connect to MongoDB, check MONGODB_URI`, go back to step 2.

---

## 6. Frontend setup

Open a **second terminal**:

```bash
cd document-assistant/frontend
npm install
cp .env.example .env               # contains VITE_API_URL=http://localhost:8000
npm run dev
```

Open the URL it prints (usually http://localhost:5173).

---

## 7. Check it works

**Backend health:**

```bash
curl http://localhost:8000/api/health
# {"status":"ok","aiProvider":"llm"}    <- "mock" means LLM_API_KEY is empty
```

**API docs:** open http://localhost:8000/docs and use "Try it out" on any endpoint.

**End to end from the command line:**

```bash
printf "Employees get 24 days of paid annual leave per year.\n" > leave-policy.txt

curl -F "file=@leave-policy.txt" http://localhost:8000/api/documents
curl http://localhost:8000/api/documents
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of annual leave do employees get?"}'
```

The chat reply should contain an `answer` and `sources` listing `leave-policy.txt`.

**In the browser:**

1. Upload a `.txt`, `.md` or `.json` file. It appears at the top of the list.
2. Click **Download** to get the original file back.
3. Ask a question about the file in the chat. The answer shows the source file under it.
4. Click **Delete** → **Yes** to remove it.
5. Try uploading a `.pdf` or an empty file and check that an error message is shown.

---

## 8. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Backend exits with `Could not connect to MongoDB, check MONGODB_URI` | MongoDB not running, wrong URI, or (Atlas) your IP not allowed | `sudo systemctl start mongod`, or fix the Atlas string / Network Access list |
| Frontend shows `Can't reach the server at http://localhost:8000` | Backend not running, or `VITE_API_URL` wrong | Start the backend. After editing `frontend/.env`, restart `npm run dev` |
| Answers are labelled **mock answer** | `LLM_API_KEY` is empty | Add the key to `backend/.env` and restart the backend |
| `AI provider rejected the API key` | Key is wrong or revoked | Create a new key on openrouter.ai |
| `AI provider is rate limiting requests` | Free model limit reached | Wait a minute, or set a different `LLM_MODEL` |
| `Address already in use` on port 8000 | Something else uses the port | Run with `--port 8001` and set `VITE_API_URL=http://localhost:8001` |
| `Unsupported file type` | Only `.txt`, `.md` and `.json` are accepted | Convert the file to one of these formats |

---

## 9. Where data is stored

| What | Where |
|---|---|
| Document info (name, size, type, date) and the extracted text | MongoDB → database `document_assistant`, collection `documents` |
| Uploaded files | `backend/data/uploads/` (random file names, the original name is kept in MongoDB) |

**Reset all data:**

```bash
mongosh "mongodb://localhost:27017/document_assistant" --eval "db.dropDatabase()"
rm -rf backend/data/uploads
```

---

## 10. Stopping

Press `Ctrl + C` in the backend and frontend terminals.
To stop local MongoDB: `sudo systemctl stop mongod`.
