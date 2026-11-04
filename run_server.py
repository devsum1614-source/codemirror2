"""
Runner for CodeMirror 2.0 Web Application
"""
import uvicorn
import os
import sys

# Ensure UTF-8 output encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure parent directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 65)
    print("[*] CodeMirror 2.0 - AI-Powered Skill Development Platform")
    print(f"    Local:   http://127.0.0.1:{port}")
    print(f"    Network: http://0.0.0.0:{port} (accessible from other devices)")
    print("=" * 65)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
