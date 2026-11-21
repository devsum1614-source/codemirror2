# Code Wizard — Online Compilers & Beginner Coding Platform

A clean, Programiz-inspired coding learning platform featuring **8 working online compilers**, **ordered beginner courses**, **Error Detective**, **Practice Labs**, and separate **Student** and **Staff/Admin** portals.

## Live Links
- **GitHub Pages:** https://devsum1614-source.github.io/codemirror2/
- **Local Full-Stack Server:** `http://127.0.0.1:8000/#languages`

## Features
- **8 Working Online Compilers:**
  - **Python** — native local Python interpreter
  - **SQL** — in-memory SQLite engine with live `Customers`, `Orders`, `resources`, and `categories` tables
  - **HTML & CSS** — live browser preview iframe
  - **JavaScript** — sandboxed browser execution & cloud sandbox
  - **C, C++, Java, TypeScript** — isolated Judge0 CE cloud sandbox (or local host compilers when installed)
- **Error Detective:** automatically diagnoses compiler, runtime, and test errors (`SyntaxError`, `IndentationError`, `NameError`, `Expected X, got None`, SQL errors, etc.) with plain-language explanations, clickable line numbers, **Give me a hint**, **Explain this error**, and **Suggest a fix** (with side-by-side diff before applying). Supports optional server-side `GEMINI_API_KEY` via `POST /api/v1/error-help`.
- **Beginner Courses:** structured 8-lesson paths (Introduction, Hello world, Variables, Input & Output, Conditions, Loops, Functions, Small Project) across Python, JavaScript, TypeScript, HTML & CSS, Java, C, and C++ with per-student saved progress.
- **Role-Based Portals:** Student accounts access Tutorials, Courses, Online Compilers, Practice Labs, Progress, and Reports; Staff (`owner` / `teacher`) accounts route exclusively to the Admin Console.

## Run Locally
```bash
pip install -r requirements.txt
python run_server.py
```
Then open **http://127.0.0.1:8000/#languages**.

## Project Structure
- `app/` — FastAPI backend, SQLite database, courses curriculum, sandbox runner, and static frontend (`app/static/`)
- `docs/` — synced static bundle for GitHub Pages (`gh-pages` branch)
- `tests/` — automated pytest suite (`python -m pytest`)
- `run_server.py` — local Uvicorn launcher
