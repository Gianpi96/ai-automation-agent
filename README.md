# ai-automation-agent

[![Build](https://img.shields.io/github/actions/workflow/status/Gianpi96/ai-automation-agent/ci.yml?branch=main&label=build&style=flat-square)](https://github.com/Gianpi96/ai-automation-agent/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?style=flat-square)](https://www.python.org)

**An AI agent that reads documents, classifies emails, and searches the web — with a real-time dashboard to watch it work.**

---

## What you get

- **Agente ReAct con Groq LLM** — l'agente usa il modello `llama-3.3-70b` via Groq per ragionare in loop: osserva, decide quale tool usare, agisce, osserva il risultato, e itera fino a 5 volte per risolvere query complesse. Non è un chatbot — è un sistema che porta a termine compiti.
- **Dashboard real-time** — interfaccia Next.js 14 con WebSocket che mostra ogni step dell'agente in diretta: quale tool sta usando, cosa ha trovato, quanto ci sta mettendo. Non una barra di caricamento — ogni azione è visibile.
- **Elaborazione documenti con OCR** — carica un PDF o DOCX (fino a 10MB) e l'agente lo legge, estrae il testo con OCR se necessario, e risponde a domande sul contenuto.
- **Agente email** — classifica i messaggi in arrivo per priorità e genera bozze di risposta. Non invia mai nulla automaticamente senza approvazione umana esplicita.
- **Ricerca web integrata** — tool `search_web` che recupera informazioni aggiornate da internet quando la risposta non è nel documento o nella memoria dell'agente.
- **13+ endpoint REST documentati** — API FastAPI con documentazione automatica su `/docs`. Ogni endpoint ha schema di input/output, esempi, e codici di errore.
- **PostgreSQL per la persistenza** — i risultati delle run, i documenti elaborati, e le classificazioni email vengono salvati e sono interrogabili. Niente si perde al riavvio.
- **Docker Compose per il deploy** — un comando avvia backend, frontend, e database insieme.

---

## Screenshots

> Aggiungi screenshot/GIF della dashboard qui: `![Agent Dashboard](docs/screenshot-dashboard.png)`

---

## Quick start

```bash
# 1. Clona e configura
git clone https://github.com/Gianpi96/ai-automation-agent
cd ai-automation-agent
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 2. Avvia tutto con Docker
docker-compose up --build
```

Frontend: `http://localhost:3000`
Backend API docs: `http://localhost:8000/docs`

Per testare l'agente direttamente:
```bash
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"query": "Search the web for the latest Next.js 15 features and summarize them"}'
```

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Example | Dove trovarla |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | `gsk_xxxxxxxxxxxx` | console.groq.com/keys |
| `GROQ_MODEL` | ✅ | `llama-3.3-70b-versatile` | Modello Groq da usare |
| `DATABASE_URL` | ✅ | `postgresql://user:pass@db/agent` | Docker Compose o esterno |
| `MAX_ITERATIONS` | ⬜ | `5` | Massimo loop ReAct (default: 5) |
| `MAX_DOCUMENT_SIZE_MB` | ⬜ | `10` | Limite upload documenti |

### Frontend (`frontend/.env.local`)

| Variable | Required | Example |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | ✅ | `ws://localhost:8000` |

---

## Architettura

```
ai-automation-agent/
├── backend/                      # FastAPI + agente IA
│   ├── agents/
│   │   ├── react_agent.py        # Loop ReAct principale
│   │   ├── document_processor.py # Elaborazione PDF/DOCX con OCR
│   │   └── email_agent.py        # Classificazione e bozze email
│   ├── tools/
│   │   ├── search_web.py         # Ricerca web
│   │   ├── read_file.py          # Lettura documenti caricati
│   │   └── send_notification.py  # Notifiche WebSocket al frontend
│   ├── services/
│   │   ├── groq_client.py        # Client LLM con retry e logging
│   │   └── cache.py              # Cache risultati per query ripetute
│   ├── routers/
│   │   ├── agent.py              # POST /run, GET /status/:id
│   │   ├── documents.py          # Upload e query documenti
│   │   └── emails.py             # Classificazione email
│   └── websocket/
│       └── manager.py            # Gestione connessioni WebSocket
│
├── frontend/                     # Next.js 14 dashboard
│   ├── app/
│   │   └── dashboard/
│   │       ├── page.tsx          # Dashboard principale
│   │       └── documents/        # Upload e gestione documenti
│   └── components/
│       ├── AgentList.tsx         # Lista run agente
│       ├── Logs.tsx              # Log real-time via WebSocket
│       ├── Stats.tsx             # Statistiche utilizzo
│       └── Notifications.tsx     # Notifiche push
│
└── docker-compose.yml            # Backend + Frontend + PostgreSQL
```

**Flusso di una run dell'agente:**

```
POST /api/agent/run { "query": "..." }
  → Avvia loop ReAct
  → Iterazione 1: LLM decide quale tool usare
  → Tool eseguito → output restituito all'LLM
  → Notifica WebSocket → dashboard si aggiorna in real-time
  → Iterazione 2-5: LLM valuta se ha abbastanza informazioni
  → Se sì: genera risposta finale
  → Salva run nel database (query, tool usati, risposta, tempo)
  → Risposta JSON con risultato + metadata
```

---

## Il loop ReAct spiegato

ReAct (Reasoning + Acting) è il pattern che differenzia un agente da una semplice chiamata LLM:

```
[Thought] Ho bisogno di cercare informazioni su X
[Action] search_web("X latest news")
[Observation] Trovati 5 risultati: ...
[Thought] Ho abbastanza informazioni, posso rispondere
[Final Answer] ...
```

L'agente non indovina — ragiona su cosa sa, decide cosa fare, verifica il risultato, e itera. Il limite di 5 iterazioni previene loop infiniti mantenendo la capacità di affrontare query complesse.

---

## Why this stack

**Groq invece di OpenAI diretta** — Groq offre latenza ~10x inferiore su modelli open-source come Llama 3.3. Per un agente che itera 5 volte per query, la latenza si moltiplica: a 500ms per chiamata invece di 5s, l'esperienza utente cambia completamente.

**WebSocket per il real-time invece di polling** — con polling ogni secondo il client farebbe 60 chiamate API al minuto per utente. WebSocket mantiene una connessione aperta e il server notifica solo quando c'è qualcosa di nuovo. Sotto carico la differenza è enorme.

**PostgreSQL per la persistenza delle run** — salvare ogni run permette di analizzare pattern di utilizzo, debuggare comportamenti anomali, e costruire funzionalità di cronologia. Con storage solo in memoria si perde tutto a ogni riavvio.

**OCR integrato per i documenti** — molti PDF sono scan di documenti fisici, non PDF nativi con testo selezionabile. Senza OCR, metà dei documenti che gli utenti caricano risulterebbero vuoti. L'OCR è trasparente — l'utente carica e basta.

---

## License

MIT
