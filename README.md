# CodeMirror 2.0: Beginner Coding-Learning Platform & Socratic Tutor

A beginner-friendly, lab-style computer science learning workspace and backend data server featuring a searchable language catalog, dedicated language curriculum pages, real-time host toolchain verification, executable multi-language sandbox, a 7-step pedagogical lab guide, server-side Gemini AI integration with offline Socratic fallback, and **real server-side authentication with session tokens, hashed passwords, and role-based access control**.

---

## 🎨 Visual Design & Palette System

The platform is built with a welcoming, readable, and accessible light aesthetic:

| Role / Element | Color Value | Purpose / Usage |
| :--- | :--- | :--- |
| **Workspace Canvas** | `#F7F8FC` | Soft, calm gray background that reduces eye fatigue during extended coding sessions. |
| **Panels & Cards** | `#FFFFFF` | Crisp white cards, editor containers, and modal dialogs with light gray borders (`#E2E8F0`). |
| **Primary Typography** | `#1B2230` | High-contrast, readable deep navy for headers, labels, and editor code text. |
| **Primary Actions** | `#4F46E5` | Indigo for interactive buttons, links, active tabs, and primary launch triggers. |
| **Progress & Success** | `#0F9F82` | Teal for completed challenges, passing tests, XP bars, and verified badges. |
| **AI Hints & Warnings**| `#D97706` | Amber for 3-stage progressive hints, toolchain warnings, and intermediate difficulty. |
| **Errors & Failures** | `#DC2626` | Red for failed test assertions, compiler syntax errors, and boundary exceptions. |

- **Responsive Layout**: Fluid flex and grid layouts tailored for desktops, laptops, tablets, and mobile devices.
- **Motion Accessibility**: Respects `@media (prefers-reduced-motion: reduce)` by disabling ambient canvas animations and confetti.
- **Accessible Typography**: High readability with `Inter` and `JetBrains Mono` font families.

---

## 🔐 Authentication, Sessions & Role Security

The platform enforces **real server-side authentication**:
- **Password Security**: Uses salted PBKDF2-HMAC-SHA256 (100,000 iterations, 16-byte random salt). Plaintext passwords are never stored or logged.
- **Session Tokens**: Generates 256-bit cryptographically secure session tokens stored in the `sessions` table in SQLite, delivered via `HttpOnly` cookie (`cm_session`) and `Authorization: Bearer <token>` header.
- **No Client Spoofing**: Client-side role selectors and editable account-ID headers are strictly eliminated for authorization. All admin endpoints verify the server-side session token and enforce role boundaries.
- **Student Registration**: Restricted strictly to `role="student"`. Admin accounts cannot be self-registered and must be provisioned by authorized owners or seeded initially.
- **Strict Data Scoping**:
  - Students can only view their own progress, attempts, and XP.
  - Instructors can only view students enrolled in their assigned classes.
  - Site Owners can manage platform-wide settings, challenges, and classes.

### Default Seeded Accounts & Passwords

| Role | Account ID / Username | Email | Default Password | Initial Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Site Owner** | `own_master_admin` / `admin` | `owner@codemirror.local` | `Admin@Pass2026!` | Platform-wide Administrator |
| **Teacher** | `tea_alan_turing` | `turing@campus.edu` | `Teacher@Pass2026!` | Instructor for `cls_cs101` |
| **Student 1** | `stu_alex_vance` | `alex.vance@campus.edu` | `Student@Pass2026!` | Enrolled in `cls_cs101` |
| **Student 2** | `stu_maya_lin` | `maya.lin@campus.edu` | `Student@Pass2026!` | Enrolled in `cls_cs101` |
| **Student 3** | `stu_kai_chen` | `kai.chen@campus.edu` | `Student@Pass2026!` | Enrolled in `cls_web200` |

---

## 🧭 Navigation & Core Features

### 1. 🚪 Login-First Landing Pages
- **Student Sign In / Sign Up (`/` or `#login`)**:
  - The default landing screen when unauthenticated.
  - Students can sign in with their email/ID and password, or create a new student account.
  - Link to the separate Admin Portal.
- **Separate Admin Portal (`/admin/login` or `#admin-login`)**:
  - Dedicated sign-in page for Site Owners and Course Instructors.
  - After signing in, owners and instructors are routed directly to the management console.

### 2. 🌐 Language Home Page (`/languages`)
- Searchable catalog of 7 programming languages: **Python, JavaScript, Java, C, C++, SQL, and HTML/CSS**.
- Real-time compiler/runtime status check (`🟢 Ready to Run` vs `🟡 Setup Guide / Missing Compiler`).
- Honest detection: never displays fake success when a compiler is missing from the server.
- Current Host Toolchain Status on this machine:
  - Python 3.12: **Ready to Run**
  - SQLite 3: **Ready to Run**
  - HTML & CSS: **Ready to Run** (Live in-browser sandboxed preview)
  - JavaScript (Node.js), Java JDK (`javac`), C (`gcc`), C++ (`g++`): Honest status notice with step-by-step setup guides for Windows, macOS, and Linux.

### 3. 📖 Dedicated Language Pages (`/languages/{lang_id}`)
Curriculum pages for each language featuring:
- Beginner lessons (syntax, variables, control flow, functions, memory models).
- Language-specific practice labs with direct "Start Coding" buttons.
- Safe syntax references.
- OS-specific compiler installation guides (`winget`, `brew`, `apt-get`).

### 4. 🧪 Coding Workspace & 7-Step Lab Guide
- **Monaco Code Editor**: Left panel with language switcher, custom `stdin` input, Reset Starter, Local Save, and Run & Submit controls.
- **7-Step Lab Guide**:
  1. *Restate the task* in your own words.
  2. *Identify inputs, outputs, rules, and constraints*.
  3. *Work through sample tests and edge cases*.
  4. *Break into plain-language steps or pseudocode*.
  5. *Write the complete program yourself*.
  6. *Run, inspect errors, and debug*.
  7. *Concept recap & practice next*.
- **Run & Output**: Automated sandbox test output with clear compiler/runtime error diagnostics, line-number pointers, and concept recaps upon success.
- **Live Preview (HTML/CSS)**: An isolated sandboxed `<iframe>` (`sandbox="allow-scripts"`) for real-time visual inspection of web markup and styles.

### 5. 🛡️ Core Learning Rule (AI Tutor, Not Code Generator)
- **Student Writes Every Line**: The AI Coach never writes, autocompletes, or replaces lab code.
- **No Cheat Buttons**: The cheat "View Solution" button has been completely eliminated.
- **Solution Requests Intercepted**: The AI tutor politely refuses requests to solve the lab and returns a guiding question instead.
- **3-Stage Progressive Hints**:
  - *Stage 1 (Question)*: Prompts student reflection on assumptions and inputs.
  - *Stage 2 (Clue)*: Explains algorithmic strategy without providing code.
  - *Stage 3 (Explanation)*: Deep dive into the underlying concept.

### 6. 🤖 Gemini AI Integration & Offline Socratic Engine
- The AI Coach connects through the server using the official Google Gemini API (default model: `gemini-1.5-flash`).
- **Server-Side API Key**: The API key is stored exclusively in the `GEMINI_API_KEY` server environment variable and is never exposed to browser code.
- **Offline Fallback**: When `GEMINI_API_KEY` is not set, the built-in local Socratic engine runs seamlessly.
- **Live AI Status Badge**: Displays real-time status in the AI Coach tab (`🟢 Live Gemini AI Active` vs `🟡 Offline Socratic Engine Active`).

### 7. 👑 Site Owner Console & Appearance Controls
- **Learning Analytics**: Pass rates, total attempts, and telemetry for common student error topics (`KeyError`, `IndexError`, `SyntaxError`).
- **Challenge Manager**: Create, edit, publish, or archive coding challenges with private server-side test suites and concept recaps.
- **Classes & Students**: View rosters and edit student profiles (display name, email, class assignment).
- **Appearance & Platform Settings**: Change site title, primary brand color (`theme_primary`), background canvas color (`theme_background`), card surface color, and AI guidance prompt.
- **Data Export**: Export a complete JSON backup of the platform (`GET /api/v1/admin/export`).

---

## 🚀 Quick Setup & Startup

### 1. Requirements
- Python 3.10+ (Tested on Python 3.12.10)
- SQLite 3 (Standard Python library)
- Dependencies: `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx`

### 2. Install Dependencies
```powershell
cd "C:\Users\SHREESHANT HADAPAD\.gemini\antigravity\scratch\codemirror2"
python -m pip install fastapi uvicorn pydantic pytest httpx
```

### 3. Configure Gemini AI (Optional)
```powershell
# In PowerShell:
$env:GEMINI_API_KEY = "your-actual-gemini-api-key"
$env:GEMINI_MODEL = "gemini-1.5-flash"
```
*(If omitted, the platform automatically runs using the built-in offline Socratic tutor engine).*

### 4. Start the Application
```powershell
python run_server.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your web browser.

### 5. Run Automated Tests
```powershell
python -m pytest tests -v
```
All **29 automated tests** verify authentication, password hashing, RBAC, sandbox safety, language routing, and Socratic coaching.

---

## 📁 Project Architecture & File Map

```
codemirror2/
├── app/
│   ├── main.py              # FastAPI server initialization, SPA routes, CORS
│   ├── auth.py              # PBKDF2-HMAC password hashing, session tokens, RBAC dependencies
│   ├── database.py          # SQLite schema (accounts, sessions, challenges, attempts, ledger, settings)
│   ├── languages.py         # Language curriculum catalog (lessons, syntax guides, toolchain setup)
│   ├── runtimes.py          # Real-time host compiler/interpreter detection (Python, SQL, HTML, JS, Java, C, C++)
│   ├── sandbox.py           # Subprocess code execution sandbox worker & HTML preview generator
│   ├── ai_coach.py          # Gemini AI API caller, Socratic progressive hints, and Core Learning Rule guard
│   ├── routes_v1.py         # Student REST API (/auth/login, /auth/register, /languages, /challenges, /attempts)
│   ├── routes_admin.py      # Role-based Admin & Owner API endpoints (/admin/overview, /admin/settings, /admin/export)
│   ├── seed_challenges.py   # Seed challenge definitions with private test suites and concept recaps
│   ├── seed_data.py         # Seeded accounts (Owner, Teacher, Students) and classes
│   ├── runner.py            # Sandbox execution coordinator
│   └── static/
│       ├── index.html       # Single-page application HTML5 interface (Auth, Catalog, Detail, Workspace, Admin)
│       ├── css/
│       │   └── style.css    # Clean palette (#F7F8FC, #4F46E5, #0F9F82), auth cards, 7-step guide
│       └── js/
│           ├── api.js       # Client API connector with session tokens and REST queries
│           ├── app.js       # UI controller, auth state management, Socratic AI Coach chat, 7-step guide rendering
│           ├── editor.js    # Monaco code editor integration (light theme)
│           └── particles.js # Ambient canvas animation (reduced-motion aware)
├── tests/
│   ├── test_platform.py     # End-to-end integration tests for core student flows
│   ├── test_v1_api.py       # REST API unit tests for sandbox, hints, and XP policies
│   ├── test_admin_and_roles.py # Tests for real session auth, RBAC, Owner CRUD, and settings configuration
│   ├── test_beginner_tutor_and_languages.py # Tests for language catalog, Socratic tutor, Core Learning Rule
│   └── test_live_server.py  # Live HTTP server test runner (12 end-to-end checks)
├── .gitignore               # Ignores __pycache__, *.db, *.log, *.pyc, *.env
├── codemirror.db            # SQLite relational database
├── run_server.py            # Development server runner
└── README.md                # Comprehensive documentation & user guide
```
