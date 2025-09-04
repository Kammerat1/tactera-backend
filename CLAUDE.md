# Claude Code Context

## Developer Profile
- **Experience Level**: Beginner - First time working with Python, React, and TailwindCSS
- **Project**: Tactera - Football management game

## Project Structure
- **Backend**: Python FastAPI in `backend/` directory
- **Frontend**: React + TypeScript + TailwindCSS in `frontend/` directory
- **Database**: SQLite for development

## Development Preferences
- Provide detailed explanations for Python, React, and TailwindCSS concepts
- Include comments in code when explaining new concepts
- Prefer step-by-step guidance for complex tasks
- Always explain what commands do before running them
- Always ask before implementing something
- Always remember to remind the user to commit and push to GitHub.
- Always remember to guide the user through testing after implementing new functionality.
- Always remember to update this document. Especially the Notes.

## Common Commands
- **Backend setup**: `cd backend && source venv/Scripts/activate`
- **Backend dev server**: `cd backend && source venv/Scripts/activate && python -m app.main`
- **Frontend dev server**: `cd frontend && npm run dev`
- **Frontend lint**: `cd frontend && npm run lint`

## Environment Setup Completed
- Python 3.11.9 with virtual environment in `backend/venv/`
- Node.js 22.19.0 with npm 10.9.3
- All dependencies installed successfully
- Backend serves API on `http://localhost:8000` (when started)
- Frontend serves on `http://localhost:5173`

## Notes
- Project was recently restructured from `tactera_backend/` and `Tactera_frontend/` to proper `backend/` and `frontend/` structure
- All Python imports updated to use `app.` prefix instead of `tactera_backend.`
- Virtual environment must be activated before running backend commands