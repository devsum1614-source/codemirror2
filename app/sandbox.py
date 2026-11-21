"""
Isolated Sandbox Execution Engine for Student Coding Quest & CodeMirror 2.0
Runs student code against private test suites or standalone examples in a disposable subprocess worker.
Enforces execution timeouts, restricted environment, and plain-language error summaries.
Guarantees we never display fake success when a language runtime is absent.
"""

import sys
import os
import re
import json
import sqlite3
import tempfile
import subprocess
from typing import Dict, Any, List, Optional

from app.runtimes import check_language_runtime

# Default sample SQL schema pre-loaded for standalone SQL examples and queries
DEFAULT_SQL_EXAMPLE_SCHEMA = """
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE resources (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    category_id INTEGER,
    status TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

INSERT INTO categories (id, name) VALUES
(1, 'STEM & Robotics'),
(2, 'Arts & Media'),
(3, 'Career Services');

INSERT INTO resources (id, title, category_id, status, created_at) VALUES
(101, '3D Printer Lab Access', 1, 'active', '2026-10-01 10:00:00'),
(102, 'Old Newsletter Archive', 2, 'archived', '2026-09-01 12:00:00'),
(103, 'Resume Review Session', 3, 'active', '2026-10-15 14:00:00'),
(104, 'VR Development Kit', 1, 'active', '2026-10-20 09:30:00');

CREATE TABLE Customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    age INTEGER,
    country TEXT
);

CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY,
    item TEXT NOT NULL,
    amount INTEGER,
    customer_id INTEGER,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

INSERT INTO Customers (customer_id, first_name, last_name, age, country) VALUES
(1, 'John', 'Doe', 31, 'USA'),
(2, 'Robert', 'Luna', 22, 'USA'),
(3, 'David', 'Robinson', 22, 'UK'),
(4, 'John', 'Reinhardt', 25, 'UK'),
(5, 'Betty', 'Doe', 28, 'UAE');

INSERT INTO Orders (order_id, item, amount, customer_id) VALUES
(1, 'Keyboard', 400, 4),
(2, 'Mouse', 300, 4),
(3, 'Monitor', 12000, 3),
(4, 'Keyboard', 400, 1),
(5, 'Mousepad', 250, 2);
"""

# Python standalone snippet runner template (blocks network access)
STANDALONE_PYTHON_RUNNER = r"""
import sys

def _block_network():
    for mod in ['socket', 'urllib', 'http', 'requests']:
        sys.modules[mod] = None

_block_network()

with open("main.py", "r", encoding="utf-8") as _f:
    _code = _f.read()

_globals = {"__name__": "__main__"}
exec(compile(_code, "main.py", "exec"), _globals)
"""

# Python / SQL challenge test worker template
WORKER_TEMPLATE_PYTHON = r"""
import sys
import json
import traceback

# Security: Block sensitive operations inside the sandbox
def _block_dangerous_builtins():
    for mod in ['socket', 'urllib', 'http', 'requests']:
        sys.modules[mod] = None

_block_dangerous_builtins()

def run():
    code_path = "student_code.py"
    with open(code_path, "r", encoding="utf-8") as f:
        student_code = f.read()

    with open("test_spec.json", "r", encoding="utf-8") as f:
        test_spec = json.load(f)

    # Execution namespace
    sandbox_globals = {"__name__": "__sandbox__"}
    
    try:
        # Compile student code
        compiled = compile(student_code, "<student_code>", "exec")
        exec(compiled, sandbox_globals)
    except SyntaxError as se:
        print(json.dumps({
            "passed": False,
            "runtime_available": True,
            "feedback": f"Syntax error at line {se.lineno}: {se.msg}",
            "error_summary": f"SyntaxError: {se.msg} (line {se.lineno})",
            "test_count": 1,
            "passed_count": 0,
            "failed_count": 1,
            "details": [{"name": "syntax_check", "passed": False, "error": f"Line {se.lineno}: {se.msg}"}]
        }))
        return
    except Exception as e:
        err_msg = str(e)
        print(json.dumps({
            "passed": False,
            "runtime_available": True,
            "feedback": f"Compilation/Import error: {err_msg}",
            "error_summary": f"{type(e).__name__}: {err_msg}",
            "test_count": 1,
            "passed_count": 0,
            "failed_count": 1,
            "details": [{"name": "import_check", "passed": False, "error": err_msg}]
        }))
        return

    # Run challenge-specific test logic
    results = []
    try:
        tests = test_spec.get("tests", [])
        for t in tests:
            t_type = t.get("type")
            t_name = t.get("name")
            
            if t_type == "function_call":
                fn_name = t.get("function")
                if fn_name not in sandbox_globals:
                    results.append({"name": t_name, "passed": False, "error": f"Function '{fn_name}' not defined in code."})
                    continue
                
                fn = sandbox_globals[fn_name]
                args = t.get("args", [])
                kwargs = t.get("kwargs", {})
                expected = t.get("expected")
                expect_exception = t.get("expect_exception")
                
                if expect_exception:
                    try:
                        fn(*args, **kwargs)
                        results.append({"name": t_name, "passed": False, "error": f"Expected {expect_exception} but none was raised."})
                    except Exception as ex:
                        if type(ex).__name__ == expect_exception or expect_exception in str(type(ex)):
                            results.append({"name": t_name, "passed": True, "error": None})
                        else:
                            results.append({"name": t_name, "passed": False, "error": f"Expected {expect_exception}, got {type(ex).__name__}: {str(ex)}"})
                else:
                    try:
                        actual = fn(*args, **kwargs)
                        if actual == expected:
                            results.append({"name": t_name, "passed": True, "error": None})
                        else:
                            results.append({"name": t_name, "passed": False, "error": f"Expected {expected}, got {actual}"})
                    except Exception as call_err:
                        results.append({"name": t_name, "passed": False, "error": f"Runtime error: {call_err}"})
                        
            elif t_type == "sql_query":
                import sqlite3
                setup_sql = t.get("setup_sql", "")
                expected_rows = t.get("expected_rows", [])
                
                db = sqlite3.connect(":memory:")
                cur = db.cursor()
                cur.executescript(setup_sql)
                
                query_str = student_code.strip()
                if query_str.endswith(";"):
                    query_str = query_str[:-1]
                    
                cur.execute(query_str)
                rows = [list(r) for r in cur.fetchall()]
                cols = [d[0].lower() for d in cur.description] if cur.description else []
                req_cols = t.get("required_cols", [])
                
                missing_cols = [c for c in req_cols if c not in cols]
                if missing_cols:
                    results.append({"name": t_name, "passed": False, "error": f"Missing required column(s): {', '.join(missing_cols)}"})
                elif len(rows) != len(expected_rows):
                    results.append({"name": t_name, "passed": False, "error": f"Expected {len(expected_rows)} rows, but query returned {len(rows)} rows."})
                else:
                    results.append({"name": t_name, "passed": True, "error": None})
                db.close()

    except Exception as e:
        print(json.dumps({
            "passed": False,
            "runtime_available": True,
            "feedback": f"Execution error in test runner: {str(e)}",
            "error_summary": f"{type(e).__name__}: {str(e)}"
        }))
        return

    passed_count = sum(1 for r in results if r["passed"])
    failed_count = len(results) - passed_count
    all_passed = failed_count == 0 and len(results) > 0
    
    first_failure = next((r for r in results if not r["passed"]), None)
    if all_passed:
        feedback = f"All {len(results)} test checks passed successfully!"
        error_summary = None
    else:
        feedback = first_failure["error"] if first_failure else "One or more tests failed."
        error_summary = f"{first_failure['name']}: {first_failure['error']}" if first_failure else "Tests failed."

    print(json.dumps({
        "passed": all_passed,
        "runtime_available": True,
        "feedback": feedback,
        "test_count": len(results),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "error_summary": error_summary,
        "details": results
    }))

if __name__ == "__main__":
    run()
"""


def _format_sql_table(columns: List[str], rows: List[Any]) -> str:
    if not columns:
        return ""
    str_rows = [[str(cell) if cell is not None else "NULL" for cell in row] for row in rows]
    widths = [len(col) for col in columns]
    for r in str_rows:
        for idx, val in enumerate(r):
            if idx < len(widths):
                widths[idx] = max(widths[idx], len(val))
    header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    sep = "-+-".join("-" * widths[i] for i in range(len(columns)))
    body = [" | ".join(r[i].ljust(widths[i]) for i in range(len(columns))) for r in str_rows]
    return "\n".join([header, sep] + body)


def _split_sql_statements(sql_text: str) -> List[str]:
    """Splits SQL script into individual statements using sqlite3.complete_statement."""
    statements: List[str] = []
    buffer: List[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") and not buffer:
            continue
        buffer.append(line)
        candidate = "\n".join(buffer)
        if sqlite3.complete_statement(candidate):
            stmt = candidate.strip()
            if stmt:
                statements.append(stmt)
            buffer = []
    remainder = "\n".join(buffer).strip()
    if remainder:
        statements.append(remainder)
    return statements


JUDGE0_LANGUAGE_IDS = {
    "c": 50,           # C (GCC 9.2.0)
    "cpp": 54,         # C++ (GCC 9.2.0)
    "java": 62,        # Java (OpenJDK 13.0.1)
    "javascript": 63,  # JavaScript (Node.js 12.14.0)
    "typescript": 74,  # TypeScript (3.7.4)
    "python": 71,      # Python (3.8.1)
}


def _execute_via_judge0(
    lang_id: str,
    lang_name: str,
    code: str,
    stdin_text: str = "",
    timeout_seconds: float = 12.0,
) -> Optional[Dict[str, Any]]:
    """
    Executes code in an isolated remote Judge0 CE sandbox when a local compiler
    is not installed on this host. Returns None if Judge0 CE is unreachable.
    """
    judge0_lang_id = JUDGE0_LANGUAGE_IDS.get(lang_id)
    if not judge0_lang_id:
        return None
    if os.environ.get("DISABLE_REMOTE_SANDBOX") == "1":
        return None

    import urllib.request

    payload = json.dumps({
        "language_id": judge0_lang_id,
        "source_code": code or "",
        "stdin": stdin_text or "",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://ce.judge0.com/submissions?base64_encoded=false&wait=true",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "CodeWizard/2.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    status_obj = data.get("status") or {}
    status_id = status_obj.get("id", 0)
    status_desc = status_obj.get("description") or "Completed"
    stdout = (data.get("stdout") or "").rstrip()
    compile_out = (data.get("compile_output") or "").strip()
    stderr = (data.get("stderr") or "").strip()
    err_parts = [p for p in (compile_out, stderr) if p]
    error_text = "\n".join(err_parts) if err_parts else (None if status_id == 3 else status_desc)
    success = (status_id == 3) and not error_text

    return {
        "language": lang_id,
        "language_name": lang_name,
        "runtime_label": f"{lang_name} Cloud Sandbox",
        "runtime_available": True,
        "status_label": "Available",
        "mode_label": "Runnable",
        "ran": True,
        "success": success,
        "output": stdout,
        "error": error_text,
    }


def execute_code_snippet(
    code: str,
    language: str = "python",
    stdin_text: str = "",
    timeout_seconds: float = 3.0,
) -> Dict[str, Any]:
    """
    Runs a standalone code example or student program in an isolated, time-limited environment
    using the language's actual compiler, interpreter, or runtime (falling back to the isolated
    Judge0 CE cloud sandbox when a local compiler is not installed).
    """
    raw_norm = (language or "python").lower().strip()
    if raw_norm in ("ts", "typescript"):
        lang_id = "typescript"
        lang_info = {
            "id": "typescript",
            "name": "TypeScript",
            "runtime_label": "TypeScript Compiler",
            "available": False,
            "setup_guide": {"title": "TypeScript Setup", "command": "tsc --version"},
        }
    else:
        lang_info = check_language_runtime(language)
        lang_id = lang_info.get("id", raw_norm)

    if not lang_info["available"]:
        remote_result = _execute_via_judge0(
            lang_id=lang_id,
            lang_name=lang_info.get("name", lang_id.upper()),
            code=code,
            stdin_text=stdin_text,
        )
        if remote_result is not None:
            return remote_result

        return {
            "language": lang_id,
            "language_name": lang_info["name"],
            "runtime_label": lang_info.get("runtime_label", lang_info["name"]),
            "runtime_available": False,
            "status_label": "Not installed",
            "mode_label": "View only",
            "ran": False,
            "success": False,
            "output": "",
            "error": (
                f"{lang_info['name']} ({lang_info.get('runtime_label', 'compiler/runtime')}) is not installed on this server "
                "and the remote sandbox could not be reached."
            ),
            "setup_guide": lang_info.get("setup_guide", {}),
        }

    # 1. HTML & CSS Browser Preview
    if lang_id == "html":
        has_markup = len((code or "").strip()) > 0
        return {
            "language": "html",
            "language_name": lang_info["name"],
            "runtime_label": lang_info.get("runtime_label", "Browser preview"),
            "runtime_available": True,
            "status_label": "Available",
            "mode_label": "Runnable",
            "ran": True,
            "success": has_markup,
            "output": "Rendered in the live browser preview.",
            "error": None if has_markup else "Enter HTML or CSS code to preview it.",
            "html_preview": code,
        }

    # 2. SQL (In-memory SQLite engine)
    if lang_id == "sql":
        conn = sqlite3.connect(":memory:")
        try:
            cur = conn.cursor()
            cur.executescript(DEFAULT_SQL_EXAMPLE_SCHEMA)
            statements = _split_sql_statements(code or "")
            if not statements:
                return {
                    "language": "sql",
                    "language_name": lang_info["name"],
                    "runtime_label": lang_info.get("runtime_label", "SQLite engine"),
                    "runtime_available": True,
                    "status_label": "Available",
                    "mode_label": "Runnable",
                    "ran": True,
                    "success": False,
                    "output": "",
                    "error": "No SQL statement found to execute.",
                }

            outputs: List[str] = []
            tables: List[Dict[str, Any]] = []
            for stmt in statements:
                cur.execute(stmt)
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
                    outputs.append(_format_sql_table(cols, rows))
                    tables.append({"columns": cols, "rows": [list(r) for r in rows]})

            conn.commit()
            final_output = "\n\n".join(outputs) if outputs else "SQL statement executed."
            return {
                "language": "sql",
                "language_name": lang_info["name"],
                "runtime_label": lang_info.get("runtime_label", "SQLite engine"),
                "runtime_available": True,
                "status_label": "Available",
                "mode_label": "Runnable",
                "ran": True,
                "success": True,
                "output": final_output,
                "tables": tables,
                "error": None,
            }
        except Exception as sql_err:
            return {
                "language": "sql",
                "language_name": lang_info["name"],
                "runtime_label": lang_info.get("runtime_label", "SQLite engine"),
                "runtime_available": True,
                "status_label": "Available",
                "mode_label": "Runnable",
                "ran": True,
                "success": False,
                "output": "",
                "error": f"SQL error: {sql_err}",
            }
        finally:
            conn.close()

    # 3. Subprocess-based compilers and interpreters (Python, JavaScript, Java, C, C++)
    clean_env = {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": "",
        "PYTHONIOENCODING": "utf-8",
    }

    with tempfile.TemporaryDirectory(prefix=f"cw_run_{lang_id}_") as temp_dir:
        try:
            if lang_id == "python":
                code_path = os.path.join(temp_dir, "main.py")
                runner_path = os.path.join(temp_dir, "_runner.py")
                with open(code_path, "w", encoding="utf-8") as f:
                    f.write(code)
                with open(runner_path, "w", encoding="utf-8") as f:
                    f.write(STANDALONE_PYTHON_RUNNER)
                run_cmd = [sys.executable, runner_path]

            elif lang_id == "javascript":
                code_path = os.path.join(temp_dir, "main.js")
                with open(code_path, "w", encoding="utf-8") as f:
                    f.write(code)
                run_cmd = [lang_info["executable"], code_path]

            elif lang_id == "java":
                match = re.search(r"public\s+class\s+([A-Za-z_][A-Za-z0-9_]*)", code) or re.search(
                    r"class\s+([A-Za-z_][A-Za-z0-9_]*)", code
                )
                class_name = match.group(1) if match else "Main"
                java_file = os.path.join(temp_dir, f"{class_name}.java")
                with open(java_file, "w", encoding="utf-8") as f:
                    f.write(code)

                compile_proc = subprocess.run(
                    [lang_info["executable"], java_file],
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout_seconds,
                    env=clean_env,
                )
                if compile_proc.returncode != 0:
                    err_text = (compile_proc.stderr or compile_proc.stdout or "Java compilation failed.").replace(
                        temp_dir, ""
                    ).strip()
                    return {
                        "language": "java",
                        "language_name": lang_info["name"],
                        "runtime_label": lang_info.get("runtime_label", "Java compiler and JVM"),
                        "runtime_available": True,
                        "status_label": "Available",
                        "mode_label": "Runnable",
                        "ran": True,
                        "success": False,
                        "output": "",
                        "error": f"Compiler error:\n{err_text}",
                    }
                java_bin = lang_info.get("java_executable") or "java"
                run_cmd = [java_bin, "-cp", temp_dir, class_name]

            elif lang_id in ("c", "cpp"):
                src_name = "main.c" if lang_id == "c" else "main.cpp"
                exe_name = "program.exe" if os.name == "nt" else "program"
                src_path = os.path.join(temp_dir, src_name)
                exe_path = os.path.join(temp_dir, exe_name)
                with open(src_path, "w", encoding="utf-8") as f:
                    f.write(code)

                compile_args = [lang_info["executable"], src_path, "-o", exe_path]
                if lang_id == "cpp":
                    compile_args = [lang_info["executable"], "-std=c++17", src_path, "-o", exe_path]

                compile_proc = subprocess.run(
                    compile_args,
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout_seconds,
                    env=clean_env,
                )
                if compile_proc.returncode != 0:
                    err_text = (compile_proc.stderr or compile_proc.stdout or "Compilation failed.").replace(
                        temp_dir, ""
                    ).strip()
                    return {
                        "language": lang_id,
                        "language_name": lang_info["name"],
                        "runtime_label": lang_info.get("runtime_label", lang_info["name"]),
                        "runtime_available": True,
                        "status_label": "Available",
                        "mode_label": "Runnable",
                        "ran": True,
                        "success": False,
                        "output": "",
                        "error": f"Compiler error:\n{err_text}",
                    }
                run_cmd = [exe_path]
            else:
                return {
                    "language": lang_id,
                    "language_name": lang_info["name"],
                    "runtime_label": lang_info.get("runtime_label", lang_info["name"]),
                    "runtime_available": False,
                    "status_label": "Not installed",
                    "mode_label": "View only",
                    "ran": False,
                    "success": False,
                    "output": "",
                    "error": f"Unsupported language runtime: {language}",
                }

            proc = subprocess.run(
                run_cmd,
                cwd=temp_dir,
                input=stdin_text or "",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                env=clean_env,
            )
            stdout_clean = (proc.stdout or "").replace(temp_dir, "<workspace>").rstrip()
            stderr_clean = (proc.stderr or "").replace(temp_dir, "<workspace>").strip()

            if proc.returncode != 0:
                # Extract concise, readable error line for beginners
                err_lines = [line for line in stderr_clean.splitlines() if "_runner.py" not in line]
                friendly_err = "\n".join(err_lines[-6:]) if err_lines else "Program exited with an error."
                return {
                    "language": lang_id,
                    "language_name": lang_info["name"],
                    "runtime_label": lang_info.get("runtime_label", lang_info["name"]),
                    "runtime_available": True,
                    "status_label": "Available",
                    "mode_label": "Runnable",
                    "ran": True,
                    "success": False,
                    "output": stdout_clean,
                    "error": friendly_err,
                }

            return {
                "language": lang_id,
                "language_name": lang_info["name"],
                "runtime_label": lang_info.get("runtime_label", lang_info["name"]),
                "runtime_available": True,
                "status_label": "Available",
                "mode_label": "Runnable",
                "ran": True,
                "success": True,
                "output": stdout_clean,
                "error": None,
            }

        except subprocess.TimeoutExpired:
            return {
                "language": lang_id,
                "language_name": lang_info["name"],
                "runtime_label": lang_info.get("runtime_label", lang_info["name"]),
                "runtime_available": True,
                "status_label": "Available",
                "mode_label": "Runnable",
                "ran": True,
                "success": False,
                "output": "",
                "error": f"Time limit exceeded ({timeout_seconds}s). Check your code for an infinite loop.",
            }
        except Exception as exc:
            return {
                "language": lang_id,
                "language_name": lang_info["name"],
                "runtime_label": lang_info.get("runtime_label", lang_info["name"]),
                "runtime_available": True,
                "status_label": "Available",
                "mode_label": "Runnable",
                "ran": True,
                "success": False,
                "output": "",
                "error": f"Execution error: {exc}",
            }


def execute_in_sandbox(
    challenge_id: str, 
    student_code: str, 
    test_spec_json: str, 
    language: str = "python", 
    timeout_seconds: float = 3.0
) -> Dict[str, Any]:
    """
    Executes student code against private test specification in a disposable,
    resource-limited subprocess worker.
    Respects host compiler availability; never returns fake success.
    """
    lang_info = check_language_runtime(language)
    
    # 1. Strictly verify runtime availability on host
    if not lang_info["available"]:
        return {
            "passed": False,
            "runtime_available": False,
            "feedback": (
                f"Runtime Notice: {lang_info.get('description', lang_info['name'] + ' execution is unavailable on this server')}. "
                f"See the '{lang_info['name']} Setup Guide' for local development. "
                "Python, SQLite, and HTML/CSS are the runnable tracks in this build."
            ),
            "error_summary": f"RuntimeUnavailable: {lang_info.get('description', lang_info['name'])}",
            "test_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "details": [{
                "name": f"{lang_info['name'].lower()}_toolchain_check",
                "passed": False,
                "error": lang_info.get("description", f"{lang_info['name']} execution is unavailable on this server.")
            }]
        }

    # 2. HTML & CSS validation
    if lang_info["name"] == "HTML & CSS" or language.lower() in ["html", "css"]:
        try:
            spec = json.loads(test_spec_json) if test_spec_json else {}
        except Exception:
            spec = {}
            
        tests = spec.get("tests", [])
        results = []
        code_lower = student_code.lower()
        
        for t in tests:
            t_name = t.get("name", "html_element_check")
            required_tags = t.get("required_tags", [])
            missing = [tag for tag in required_tags if f"<{tag}" not in code_lower and tag not in code_lower]
            if missing:
                results.append({"name": t_name, "passed": False, "error": f"Missing required HTML element: {', '.join(missing)}"})
            else:
                results.append({"name": t_name, "passed": True, "error": None})
                
        if not results:
            # Basic sanity check
            has_content = len(student_code.strip()) > 10
            results.append({
                "name": "html_structure_check",
                "passed": has_content,
                "error": None if has_content else "HTML document is empty or incomplete."
            })
            
        passed_count = sum(1 for r in results if r["passed"])
        failed_count = len(results) - passed_count
        all_passed = failed_count == 0
        
        return {
            "passed": all_passed,
            "runtime_available": True,
            "feedback": "All HTML structure checks passed!" if all_passed else "Some HTML requirements are missing.",
            "test_count": len(results),
            "passed_count": passed_count,
            "failed_count": failed_count,
            "error_summary": None if all_passed else "HTML validation issues detected.",
            "details": results,
            "html_preview": student_code
        }

    # 3. Python & SQL Sandbox Execution
    with tempfile.TemporaryDirectory(prefix="quest_sandbox_") as temp_dir:
        code_file = os.path.join(temp_dir, "student_code.py")
        test_file = os.path.join(temp_dir, "test_spec.json")
        worker_file = os.path.join(temp_dir, "worker.py")

        with open(code_file, "w", encoding="utf-8") as f:
            f.write(student_code)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_spec_json)

        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(WORKER_TEMPLATE_PYTHON)

        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": "",
            "PYTHONIOENCODING": "utf-8"
        }

        try:
            proc = subprocess.Popen(
                [sys.executable, worker_file],
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=clean_env
            )

            stdout, stderr = proc.communicate(timeout=timeout_seconds)

            if proc.returncode != 0 and not stdout:
                clean_stderr = stderr.strip().replace(temp_dir, "<sandbox>")
                return {
                    "passed": False,
                    "runtime_available": True,
                    "feedback": "Execution error during sandbox test run.",
                    "error_summary": clean_stderr[:200] if clean_stderr else "Worker process exited abnormally."
                }

            # Parse JSON output from worker
            output_lines = [l.strip() for l in stdout.splitlines() if l.strip()]
            for line in reversed(output_lines):
                try:
                    data = json.loads(line)
                    if isinstance(data, dict) and "passed" in data:
                        return data
                except json.JSONDecodeError:
                    continue

            return {
                "passed": False,
                "runtime_available": True,
                "feedback": "Unable to verify test outcomes.",
                "error_summary": "Sandbox worker returned non-JSON output."
            }

        except subprocess.TimeoutExpired:
            proc.kill()
            return {
                "passed": False,
                "runtime_available": True,
                "feedback": f"Execution timed out ({timeout_seconds}s limit exceeded). Check for infinite loops.",
                "error_summary": "TimeoutExpired: Operation exceeded allowable execution time."
            }
        except Exception as e:
            return {
                "passed": False,
                "runtime_available": True,
                "feedback": "Internal sandbox error.",
                "error_summary": f"SandboxException: {str(e)}"
            }
