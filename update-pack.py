import os
import sys
import subprocess

"""
TODO:
Runtime
- create venv(s) in script if they don't already exist. 
- check venv locations, will be relative to this script.

GitHub
- needs to prompt a token creation, similar to intellij
- needs to be able to pull and push safely, ideally warning of any conflicts when pushing, before pushing. - Could use PRs to reolve conflicts?

General
- config system (config.yml)

"""

def restart_in_venv():
    script_path = os.path.abspath(__file__)
    base = os.path.dirname(script_path)

    if os.name == "nt":
        vpython = os.path.join(base, "venv", "Scripts", "python.exe")
    else:
        vpython = os.path.join(base, "venv", "bin", "python")

    # If already in the venv, do nothing
    if os.path.abspath(sys.executable) == os.path.abspath(vpython):
        return

    # Safety: if the venv interpreter doesn't exist, stop with a clear error
    if not os.path.exists(vpython):
        print(f" Expected venv interpreter not found at: {vpython}")
        print("   Create it with: python -m venv venv")
        sys.exit(2)

    # Relaunch using the venv Python
    completed = subprocess.run([vpython, script_path, *sys.argv[1:]])
    # Pass up child exit code, and STOP this (parent) process
    sys.exit(completed.returncode)

def in_venv():
    return (
        hasattr(sys, 'real_prefix') or
        sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    )

if not in_venv():
    restart_in_venv()
else:
    print("venv detected - continuing")

# ------------------ Main Code here ------------------ 
