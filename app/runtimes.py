"""
Language Runtime Detector for Student Coding Quest & CodeMirror 2.0
Inspects host environment for available compilers and interpreters.
Supports Python, JavaScript, C, C++, Java, SQL, and HTML/CSS.
Ensures we never display fake success when a runtime is absent.
"""

import sys
import shutil
import sqlite3
from typing import Dict, Any

def get_available_runtimes() -> Dict[str, Dict[str, Any]]:
    gcc_path = shutil.which("gcc") or shutil.which("clang") or shutil.which("cl")
    gpp_path = shutil.which("g++") or shutil.which("clang++") or shutil.which("cl")
    node_path = shutil.which("node")
    javac_path = shutil.which("javac")
    java_path = shutil.which("java")
    python_path = sys.executable

    return {
        "python": {
            "name": "Python",
            "available": True,
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "executable": python_path,
            "description": "Native execution in isolated subprocess worker",
            "file_ext": ".py"
        },
        "sql": {
            "name": "SQL (SQLite)",
            "available": True,
            "version": sqlite3.sqlite_version,
            "executable": "Built-in SQLite 3",
            "description": "In-memory isolated SQLite engine",
            "file_ext": ".sql"
        },
        "html": {
            "name": "HTML & CSS",
            "available": True,
            "version": "HTML5 / CSS3",
            "executable": "Web Browser Engine",
            "description": "Client-side sandboxed iframe preview",
            "file_ext": ".html"
        },
        "javascript": {
            "name": "JavaScript",
            "available": bool(node_path),
            "version": "Node.js detected" if node_path else None,
            "executable": node_path,
            "description": "Node.js runtime is ready" if node_path else "Node.js compiler/runtime is not installed or not found on host PATH",
            "file_ext": ".js"
        },
        "java": {
            "name": "Java",
            "available": bool(javac_path and java_path),
            "version": "Java JDK detected" if javac_path and java_path else None,
            "executable": javac_path,
            "description": "Java JDK compiler is ready" if javac_path and java_path else "Java JDK compiler is not installed or not found on host PATH",
            "file_ext": ".java"
        },
        "c": {
            "name": "C",
            "available": bool(gcc_path),
            "version": "GCC/Clang detected" if gcc_path else None,
            "executable": gcc_path,
            "description": "C compiler (GCC/Clang) is ready" if gcc_path else "C compiler is not installed or not found on host PATH",
            "file_ext": ".c"
        },
        "cpp": {
            "name": "C++",
            "available": bool(gpp_path),
            "version": "G++/Clang++ detected" if gpp_path else None,
            "executable": gpp_path,
            "description": "C++ compiler (G++) is ready" if gpp_path else "C++ compiler is not installed or not found on host PATH",
            "file_ext": ".cpp"
        }
    }

def check_language_runtime(language: str) -> Dict[str, Any]:
    norm = (language or "python").lower().strip()
    if norm in ["py", "python", "python3"]:
        norm = "python"
    elif norm in ["sql", "sqlite", "sqlite3"]:
        norm = "sql"
    elif norm in ["html", "css", "web", "html5"]:
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
    return runtimes.get(norm, {
        "name": language,
        "available": False,
        "version": None,
        "executable": None,
        "description": f"No runtime adapter registered for {language}",
        "file_ext": ".txt"
    })
