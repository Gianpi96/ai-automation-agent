# AI Automation Agent

Sistema di agenti AI basato su Groq LLM (`llama-3.3-70b-versatile`) con loop ReAct, processing documenti, automazione email e dashboard Next.js 14.

---

## Architettura

```
ai-automation-agent/
├── backend/              # FastAPI + Python 3.12
│   ├── app/
│   │   ├── main.py       # Entry point FastAPI
│   │   ├── config.py     # Settings (pydantic-settings)
│   │   ├── agents/       # ReAct, Document, Email agents
│   │   ├── tools/        # search_web, read_file, send_notification
│   │   ├── services/     # Groq client, cache, document processor
│   │   ├── models/       # Pydantic models
│   │   └── routers/      # FastAPI routers + WebSocket
│   └── tests/            # pytest (SQLite in-memory)
├── frontend/             # Next.js 14 + Tailwind CSS
│   └── src/
│       ├── app/          # App Router
│       ├── components/   # AgentList, Logs, Stats, Notifications
│       └── lib/          # API client, WebSocket manager
└── docker-compose.yml    # PostgreSQL + Backend + Frontend
```

---

## Prerequisiti

- **Python 3.12+** (nota: il Dockerfile usa 3.12-slim per compatibilità librerie)
- **Node.js 20+**
- **Docker + Docker Compose** (per PostgreSQL)
- **Chiave API Groq**: [console.groq.com](https://console.groq.com)

---

## Setup Passo per Passo

### 1. Clonare / inizializzare il repo

```bash
# Se è già presente la cartella:
cd "C:\Users\ingra\Desktop\python projects\ai-automation-agent"
git init
git add .
git commit -m "feat: initial project setup - ReAct agent, document processor, email agent, Next.js dashboard"
```

### 2. Configurare le variabili d'ambiente

```bash
# Il file .env è già presente con la chiave Groq configurata
# Per modificarlo:
notepad backend\.env
```

Variabili principali:
```env
GROQ_API_KEY=gsk_...           # La tua chiave Groq
GROQ_MODEL=llama-3.3-70b-versatile
REACT_MAX_ITERATIONS=5         # Max iterazioni loop ReAct
REACT_TIMEOUT=30               # Timeout globale (secondi)
GROQ_TIMEOUT=10                # Timeout singola chiamata Groq
```

### 3. Backend — installazione locale

```bash
cd backend

# Crea virtualenv
python -m venv .venv
.venv\Scripts\activate         # Windows PowerShell

# Installa dipendenze
pip install -r requirements.txt

# Avvia il server
uvicorn app.main:app --reload --port 8000
```

Il server sarà disponibile su: http://localhost:8000
Documentazione API: http://localhost:8000/docs

### 4. Frontend — installazione

```bash
cd frontend
npm install
npm run dev
```

La dashboard sarà disponibile su: http://localhost:3000

### 5. Con Docker (Backend + Frontend + PostgreSQL)

```bash
# Dalla root del progetto:
docker-compose up --build

# In background:
docker-compose up -d --build

# Stop:
docker-compose down
```

---

## Test Passo per Passo

### Test 1: Avviare il backend e verificare health

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload

# In altro terminale:
curl http://localhost:8000/health
# Output atteso: {"status":"healthy"}

curl http://localhost:8000/api/agent/tools
# Output atteso: lista di search_web, read_file, send_notification
```

### Test 2: Loop ReAct con 2 tool consecutivi

```bash
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Cerca notizie su Python e inviami una notifica con il risultato\"}"
```

Output atteso (JSON):
```json
{
  "answer": "...",
  "tools_used": ["search_web", "send_notification"],
  "iterations": 2,
  "confidence": 0.85,
  "status": "completed"
}
```

### Test 3: max_iterations rispettato

```bash
# Il parametro REACT_MAX_ITERATIONS=5 nel .env limita le iterazioni
# I test automatici verificano questo:
cd backend
pytest tests/test_react_agent.py::test_react_max_iterations_respected -v
```

### Test 4: Upload documento PDF

```bash
# Crea un PDF di test (serve un file PDF reale)
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test_document.pdf"

# Upload file > 10MB → deve restituire 413
# (crea un file finto)
python -c "open('big.pdf', 'wb').write(b'x' * (10*1024*1024 + 1))"
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@big.pdf"
# Atteso: {"detail":"File too large. Max size is 10MB."}
```

### Test 5: Email agent (classificazione + bozza)

```bash
# Vedi le email simulate nell'inbox
curl http://localhost:8000/api/emails/inbox

# Processa l'email di reclamo
curl -X POST http://localhost:8000/api/emails/process/email_001

# Output: classificazione + bozza con approved=false
# La bozza NON viene mai inviata automaticamente!

# Approva la bozza manualmente (usa il draft_id dal response)
curl -X POST http://localhost:8000/api/emails/drafts/{DRAFT_ID}/approve \
  -H "Content-Type: application/json" \
  -d "{\"approved\": true}"
```

### Test 6: Eseguire tutti i test automatici

```bash
cd backend
pytest -v

# Test specifici:
pytest tests/test_react_agent.py -v           # Test agente ReAct
pytest tests/test_document.py -v             # Test upload documenti
pytest tests/test_email_agent.py -v          # Test email agent

# Con coverage:
pytest --cov=app tests/ -v
```

### Test 7: WebSocket notifiche in tempo reale

Apri due tab nel browser su http://localhost:3000.
Il pannello delle notifiche (icona campanella in alto a destra) mostra:
- Status connessione WebSocket (verde = connesso)
- Notifiche in tempo reale da tutti i tab

Per testare:
```javascript
// Nella console del browser:
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({type: 'ping'}));
// Atteso: {type: 'pong', timestamp: '...'}
```

---

## API Reference

### Agente ReAct
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | `/api/agent/run` | Esegui il loop ReAct |
| GET | `/api/agent/tools` | Lista tool disponibili |

### Documenti
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload PDF/DOCX (max 10MB) |
| POST | `/api/documents/query` | Query su documento caricato |

### Email
| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/emails/inbox` | Email simulate in arrivo |
| POST | `/api/emails/process/{id}` | Classifica + genera bozza |
| POST | `/api/emails/process-all` | Processa tutto l'inbox |
| POST | `/api/emails/drafts/{id}/approve` | Approva/rifiuta bozza |
| GET | `/api/emails/drafts` | Lista tutte le bozze |

### WebSocket
| Endpoint | Descrizione |
|----------|-------------|
| `ws://localhost:8000/ws` | Notifiche real-time |

---

## Come fare il primo commit Git

```bash
# Dalla root del progetto
cd "C:\Users\ingra\Desktop\python projects\ai-automation-agent"

# 1. Inizializza il repository
git init

# 2. Configura identità (solo la prima volta)
git config user.name "Il Tuo Nome"
git config user.email "tua@email.com"

# 3. Aggiungi tutti i file (il .gitignore esclude .env, node_modules, etc.)
git add .

# 4. Verifica cosa viene aggiunto
git status

# 5. Primo commit
git commit -m "feat: initial setup - ReAct agent + document processor + email agent + Next.js dashboard"

# 6. (Opzionale) Collega a GitHub
git remote add origin https://github.com/TUO_USERNAME/ai-automation-agent.git
git branch -M main
git push -u origin main
```

### Workflow quotidiano

```bash
# Crea un branch per nuove feature
git checkout -b feat/nuova-feature

# Fai le modifiche, poi:
git add .
git commit -m "feat: descrizione della feature"

# Torna a main e mergia
git checkout main
git merge feat/nuova-feature

# Push su GitHub
git push
```

---

## Struttura dei Model Pydantic

### AgentResult
```python
class AgentResult(BaseModel):
    answer: str              # Risposta finale dell'agente
    tools_used: list[str]    # Tool chiamati durante il loop
    iterations: int          # Numero di iterazioni usate (max 5)
    confidence: float        # Confidenza 0.0-1.0
    status: AgentStatus      # completed | failed | timeout
    tool_calls: list[ToolCall]  # Dettaglio ogni chiamata tool
    total_duration_ms: int   # Durata totale in ms
```

### EmailDraft (mai auto-inviata)
```python
class EmailDraft(BaseModel):
    draft_id: str
    subject: str
    body: str
    approved: bool = False   # Sempre False finché umano non approva
    approved_at: datetime | None = None
```

---

## Troubleshooting

**`ModuleNotFoundError: groq`**
```bash
pip install -r requirements.txt
```

**`pytesseract.pytesseract.TesseractNotFoundError`**
```bash
# Windows: scarica installer da https://github.com/UB-Mannheim/tesseract/wiki
# Poi aggiungi al PATH: C:\Program Files\Tesseract-OCR
```

**`APIAuthenticationError` da Groq**
- Verifica `GROQ_API_KEY` nel file `backend/.env`
- Controlla che la chiave sia valida su console.groq.com

**Port 8000 già in uso**
```bash
# Trova il processo
netstat -ano | findstr :8000
# Termina il processo con il PID trovato
taskkill /PID <PID> /F
```
