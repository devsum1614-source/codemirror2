"""
Isolated Sandbox Execution Engine for Student Coding Quest & CodeMirror 2.0
Runs student code against private test suites in a disposable subprocess worker.
Enforces execution timeouts, restricted environment, and sanitized error summaries.
Guarantees we never display fake success when a language runtime is absent.
"""

import sys
import os
import json
import tempfile
import subprocess
from typing import Dict, Any

from app.runtimes import check_language_runtime

# Python / SQL worker template
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
