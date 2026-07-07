# Chitra AI V4 — PRD & Build Log

## Original Problem Statement
Build **Chitra**, a Chat-First Job-Centric AI Workspace. The app must feel
like ChatGPT for careers — almost every action begins and ends inside the
AI Chat. Users ask Chitra for jobs, resume help, ATS analysis, interview
prep and career roadmaps. Job search results appear as inline Job Cards
inside the conversation. Clicking a card opens an AI Workspace at
`/jobs/:jobId` showing Success Probability, ATS Score, Resume Match,
Missing Skills, Action Plan, Resume AI, Interview AI and Skill AI.

## User Choices (verbatim)
- **AI Providers** — Gemini 2.5 Flash (primary) + OpenAI GPT-5.5 (fallback).
  User-supplied API keys, stored only in backend `.env`.
- **Database** — Final target is Supabase. For V1 use MongoDB **behind a
  Repository layer** so the switch later is contained.
- **Auth** — Email+Password *and* Google login, modular for Supabase Auth later.
- **Job Search** — AI-generated realistic jobs for V1, architected to plug
  in LinkedIn / JSearch / Adzuna / Indeed / Naukri / Wellfound / Google
  Jobs later without UI/business-logic changes.
- **Resume** — PDF + DOCX + Drag&Drop + Paste, extracted text powers ATS,
  match score, interview prep, skill gaps, success probability.
- **Design** — Keep Chitra branding, blue/purple gradients, dark mode,
  rounded cards, modern glass UI, no redesign.

## Architecture
- **Backend**: FastAPI + Motor (MongoDB). All collections accessed through
  a single `Repository` class (`backend/database.py`) → Supabase swap later.
- **AI Orchestrator** (`backend/ai/providers.py`):
  - `BaseProvider` interface (`complete` method)
  - `GeminiProvider`, `OpenAIProvider` (registry-based, drop-in for Claude/Grok/DeepSeek)
  - Smart routing: Gemini for analytical tasks, OpenAI for writing tasks
  - Three-tier silent fallback: primary → fallback → Emergent emergency key
  - Robust JSON repair (`_safe_json` walks the string and balances braces)
  - HTTP 503 (not 500) when the whole chain fails
- **Frontend**: React 19 + react-router-dom v7 + Framer Motion + Tailwind +
  shadcn/ui. Outfit / Plus Jakarta Sans / JetBrains Mono fonts.
- **Routes**:
  - `GET  /api/health`
  - `POST /api/auth/register`, `POST /api/auth/login`, `POST /api`, `GET /api/auth/me`, `POST /api/auth/logout`
  - `GET/POST /api//auth/google/sessionchat/sessions`, `GET /api/chat/sessions/{id}/messages`, `DELETE /api/chat/sessions/{id}`
  - `POST /api/chat/send`
  - `GET /api/jobs/saved`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/save`, `DELETE /api/jobs/{id}/save`
  - `GET /api/jobs/{id}/analysis`, `POST /api/jobs/{id}/analysis/refresh`
  - `GET /api/resume/active`, `GET /api/resume/all`, `POST /api/resume/upload`, `POST /api/resume/paste`, `DELETE /api/resume/{id}`
  - `GET/PATCH /api/settings`
- **MongoDB Collections (Supabase-compatible names)**:
  `profiles`, `chat_sessions`, `chat_messages`, `saved_jobs`, `jobs_cache`,
  `resumes`, `career_roadmaps`, `interview_progress`, `settings`,
  `user_memories`, `job_search_history`, `user_sessions`, `job_analyses`.

## Frontend Pages
- `/login` — Email+Password + Google login.
- `/` — **Chat is the homepage**: large welcome header, big glass chat
  card, conversation, quick action chips, sidebar with recent chats +
  saved jobs + resume status.
- `/jobs/:jobId` — AI Workspace with Success Probability ring, ATS Score,
  Resume Match + tabs (Action Plan, Resume AI, Interview AI, Skill AI).
- `/settings` — Account, AI Provider preference, Sign out.

## What's Been Implemented (Jun 25, 2026)
- Chat-first home with inline Job Cards rendered inside messages
- Job Workspace with SuccessRing, ATS/Match meters, 4 tabs of AI analysis
- Quick Actions: 13 chips wired to `quick_action` intent on chat send
- Resume upload (PDF/DOCX/Paste/Drag-Drop) → text extraction → AI uses it
- Email+Password auth (JWT) + Emergent Google OAuth (cookie)
- AI Orchestrator with 3-tier fallback + robust JSON parsing
- Settings page to pin provider, sign out
- Modular Repository pattern for clean Supabase migration

## Known Caveats
- The user-provided OpenAI and Gemini keys are at/near their free-tier
  quota; the Emergent emergency fallback keeps the app working in the
  meantime. Top up the user keys (or replace them) to take over fully.
- Job search uses AI-generated listings — when a real Job API key is
  added, only `_compute` in jobs and a new fetcher in `services/` need
  changes; the UI is unaffected.

## Future Integrations (scaffolded, plug-and-play ready)
- LinkedIn / JSearch / Adzuna / Naukri / Wellfound / Google Jobs
- Claude / Grok / DeepSeek / OpenRouter (just add a Provider class)
- n8n / MCP / WhatsApp / Voice assistant
- Supabase migration (swap `Repository` implementation)

## Test Credentials
See `/app/memory/test_credentials.md`.

## Backlog (P0 / P1 / P2)
- P0: Streaming chat responses (currently single-shot)
- P0: Replace AI-generated jobs with a real Job API (LinkedIn/JSearch)
- P1: Persist career_roadmaps and interview_progress through dedicated routes
- P1: Voice input on chat (Whisper)
- P2: Cover letter PDF export, resume PDF export
- P2: Pricing/Stripe gate for premium analyses
