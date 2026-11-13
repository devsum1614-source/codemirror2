"""
Language Runtime Detector for Student Coding Quest & CodeMirror 2.0
Inspects host environment for available compilers and interpreters.
Supports Python, SQL (SQLite), HTML/CSS, JavaScript, Java, C, and C++.
Ensures we never display fake success when a runtime is absent.
"""

import sys
import shutil
import sqlite3
import subprocess
from typing import Dict, Any


def _probe_version(cmd_args: list[str]) -> str | None:
    """Safely probes a binary for its version string with a short timeout."""
    try:
        proc = subprocess.run(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1.5,
            check=False,
        )
        output = (proc.stdout or proc.stderr or "").strip()
        if proc.returncode == 0 and output:
            return output.splitlines()[0][:80]
    except Exception:
        pass
    return None


def get_available_runtimes() -> Dict[str, Dict[str, Any]]:
    gcc_path = shutil.which("gcc") or shutil.which("clang")
    gpp_path = shutil.which("g++") or shutil.which("clang++")
    node_path = shutil.which("node")
    javac_path = shutil.which("javac")
    java_path = shutil.which("java")
    python_path = sys.executable

    node_avail = bool(node_path)
    java_avail = bool(javac_path and java_path)
    c_avail = bool(gcc_path)
    cpp_avail = bool(gpp_path)

    return {
        "python": {
            "id": "python",
            "name": "Python",
            "runtime_label": "Python interpreter",
            "available": True,
            "status_label": "Available",
            "mode_label": "Runnable",
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "executable": python_path,
            "description": "Python interpreter is available and runs in an isolated subprocess.",
            "file_ext": ".py",
            "setup_guide": {
                "title": "Python 3 Interpreter Setup",
                "instructions": (
                    "Python is installed and available on this server. "
                    "For local use, install Python 3.10+ from python.org and enable 'Add python.exe to PATH'."
                ),
                "command": "python --version",
            },
        },
        "sql": {
            "id": "sql",
            "name": "SQL (SQLite)",
            "runtime_label": "SQLite engine",
            "available": True,
            "status_label": "Available",
            "mode_label": "Runnable",
            "version": sqlite3.sqlite_version,
            "executable": "Built-in SQLite 3",
            "description": "In-memory isolated SQLite engine is available.",
            "file_ext": ".sql",
            "setup_guide": {
                "title": "SQLite Engine Setup",
                "instructions": (
                    "SQLite is built into Python's standard library and runs in an isolated in-memory database."
                ),
                "command": "python -c \"import sqlite3; print(sqlite3.sqlite_version)\"",
            },
        },
        "html": {
            "id": "html",
            "name": "HTML & CSS",
            "runtime_label": "Browser preview",
            "available": True,
            "status_label": "Available",
            "mode_label": "Runnable",
            "version": "HTML5 / CSS3",
            "executable": "Sandboxed Browser Preview",
            "description": "Client-side sandboxed iframe preview is available.",
            "file_ext": ".html",
            "setup_guide": {
                "title": "HTML & CSS Browser Preview",
                "instructions": "HTML and CSS render directly inside the isolated browser preview frame.",
                "command": "Built into your web browser",
            },
        },
        "javascript": {
            "id": "javascript",
            "name": "JavaScript",
            "runtime_label": "JavaScript runtime (Node.js)",
            "available": node_avail,
            "status_label": "Available" if node_avail else "Not installed",
            "mode_label": "Runnable" if node_avail else "View only",
            "version": (_probe_version([node_path, "--version"]) or "Node.js detected") if node_avail else None,
            "executable": node_path,
            "description": (
                "Node.js runtime is available."
                if node_avail
                else "Node.js compiler/runtime is not installed or not found on host PATH"
            ),
            "file_ext": ".js",
            "setup_guide": {
                "title": "JavaScript Runtime (Node.js) Setup",
                "instructions": (
                    "Install Node.js LTS from https://nodejs.org and make sure 'node' is on your system PATH."
                ),
                "command": "node --version",
            },
        },
        "java": {
            "id": "java",
            "name": "Java",
            "runtime_label": "Java compiler and JVM",
            "available": java_avail,
            "status_label": "Available" if java_avail else "Not installed",
            "mode_label": "Runnable" if java_avail else "View only",
            "version": (_probe_version([javac_path, "-version"]) or "Java JDK detected") if java_avail else None,
            "executable": javac_path,
            "java_executable": java_path,
            "description": (
                "Java compiler (javac) and JVM (java) are available."
                if java_avail
                else "Java JDK compiler is not installed or not found on host PATH"
            ),
            "file_ext": ".java",
            "setup_guide": {
                "title": "Java Development Kit (JDK) Setup",
                "instructions": (
                    "Install OpenJDK (17 or 21+) from https://adoptium.net and add its bin folder (containing javac and java) to your PATH."
                ),
                "command": "javac -version && java -version",
            },
        },
        "c": {
            "id": "c",
            "name": "C",
            "runtime_label": "C compiler (GCC / Clang)",
            "available": c_avail,
            "status_label": "Available" if c_avail else "Not installed",
            "mode_label": "Runnable" if c_avail else "View only",
            "version": (_probe_version([gcc_path, "--version"]) or "C compiler detected") if c_avail else None,
            "executable": gcc_path,
            "description": (
                "C compiler (GCC/Clang) is available."
                if c_avail
                else "C compiler is not installed or not found on host PATH"
            ),
            "file_ext": ".c",
            "setup_guide": {
                "title": "C Compiler (GCC / Clang) Setup",
                "instructions": (
                    "Install GCC (via MinGW-w64 / w64devkit on Windows, build-essential on Linux, or Xcode Command Line Tools on macOS) and add 'gcc' to your system PATH."
                ),
                "command": "gcc --version",
            },
        },
        "cpp": {
            "id": "cpp",
            "name": "C++",
            "runtime_label": "C++ compiler (G++ / Clang++)",
            "available": cpp_avail,
            "status_label": "Available" if cpp_avail else "Not installed",
            "mode_label": "Runnable" if cpp_avail else "View only",
            "version": (_probe_version([gpp_path, "--version"]) or "C++ compiler detected") if cpp_avail else None,
            "executable": gpp_path,
            "description": (
                "C++ compiler (G++/Clang++) is available."
                if cpp_avail
                else "C++ compiler is not installed or not found on host PATH"
            ),
            "file_ext": ".cpp",
            "setup_guide": {
                "title": "C++ Compiler (G++ / Clang++) Setup",
                "instructions": (
                    "Install G++ or Clang++ (via MinGW-w64 / w64devkit on Windows, g++ on Linux, or clang++ on macOS) and add 'g++' to your system PATH."
                ),
                "command": "g++ --version",
            },
        },
    }


def check_language_runtime(language: str) -> Dict[str, Any]:
    norm = (language or "python").lower().strip()
    if norm in ["py", "python", "python3"]:
        norm = "python"
    elif norm in ["sql", "sqlite", "sqlite3"]:
        norm = "sql"
    elif norm in ["html", "css", "web", "html5", "html/css"]:
        norm = "html"
    elif norm in ["js", "javascript", "node"]:
        norm = "javascript"
    elif norm in ["java", "jdk"]:
        norm = "java"
    elif norm in ["c"]:
        norm = "c"
    elif norm in ["cpp", "c++", "cplusplus"]:
        norm = "cpp"

    runtimes = get_available_runtimes()
    return runtimes.get(
        norm,
        {
            "id": norm,
            "name": language,
            "runtime_label": f"{language} runtime",
            "available": False,
            "status_label": "Not installed",
            "mode_label": "View only",
            "version": None,
            "executable": None,
            "description": f"No runtime adapter registered for {language}",
            "file_ext": ".txt",
            "setup_guide": {
                "title": f"{language} Setup",
                "instructions": f"Install a local compiler or interpreter for {language}.",
                "command": f"{norm} --version",
            },
        },
    )
