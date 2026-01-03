# HireEdgeAI Resume Builder - FastAPI Backend

FastAPI backend for the Resume Builder application.

## Features

- Session Management with version history
- LaTeX compilation to PDF
- AI-powered resume editing
- Document conversion (PDF/DOCX to LaTeX)
- ATS scoring (Universal, HBPS, JD-specific)
- Section-based editing
- Chat interface for conversational editing

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
HOST=0.0.0.0
PORT=8000
DEBUG=True
FRONTEND_URL=http://localhost:3000
```

## Running

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Session
- `POST /api/resume/session/create` - Create session
- `GET /api/resume/session/{session_id}/state` - Get session state

### LaTeX
- `GET /api/resume/session/{session_id}/latex` - Get LaTeX source
- `PUT /api/resume/session/{session_id}/latex` - Update LaTeX
- `GET /api/resume/session/{session_id}/undo/status` - Check undo availability
- `GET /api/resume/session/{session_id}/redo/status` - Check redo availability
- `POST /api/resume/session/{session_id}/undo` - Undo change
- `POST /api/resume/session/{session_id}/redo` - Redo change
- `GET /api/resume/session/{session_id}/needs-recompile` - Check if recompile needed

### PDF
- `POST /api/resume/session/{session_id}/compile` - Compile LaTeX to PDF
- `GET /api/resume/session/{session_id}/pdf` - Download PDF

### Sections
- `GET /api/resume/session/{session_id}/sections` - List sections
- `POST /api/resume/session/{session_id}/sections/select` - Select section
- `GET /api/resume/session/{session_id}/sections/selected` - Get selected section
- `DELETE /api/resume/session/{session_id}/sections/selected` - Clear selection
- `POST /api/resume/session/{session_id}/sections/edit` - Edit section with AI

### Chat
- `POST /api/resume/session/{session_id}/chat` - Chat with AI
- `GET /api/resume/session/{session_id}/chat/history` - Get chat history
- `GET /api/resume/session/{session_id}/chat/context` - Get chat context
- `DELETE /api/resume/session/{session_id}/chat/history` - Clear chat history

### Job Description
- `PUT /api/resume/session/{session_id}/job-description` - Set job description
- `GET /api/resume/session/{session_id}/job-description` - Get job description
- `DELETE /api/resume/session/{session_id}/job-description` - Clear job description

### Upload & Download
- `POST /api/resume/session/{session_id}/upload` - Upload document (PDF/DOCX/TEX)
- `GET /api/resume/session/{session_id}/download/tex` - Download LaTeX file
- `GET /api/resume/session/{session_id}/download/zip` - Download ZIP (TEX + PDF)

### Scoring
- `POST /api/resume/session/{session_id}/score` - Calculate ATS scores

### Utilities
- `GET /api/resume/check-dependencies` - Check system dependencies

## Session Management

Sessions are stored in-memory by default. For production, consider Redis or database persistence.
