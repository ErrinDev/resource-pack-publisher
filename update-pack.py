import os
import sys
import subprocess
import shutil

"""
TODO:
Runtime
- create venv(s) in script if they don't already exist. ✓
- check venv locations, will be relative to this script. ✓

GitHub
- needs to prompt a token creation, similar to intellij
- needs to be able to pull and push safely, ideally warning of any conflicts when pushing, before pushing. - Could use PRs to reolve conflicts?

General
- config system (config.yml)

"""

def setup_venv():
    script_path = os.path.abspath(__file__)
    base = os.path.dirname(script_path)

    if os.name == "nt":
        vpython = os.path.join(base, "venv", "Scripts", "python.exe")
    else:
        vpython = os.path.join(base, "venv", "bin", "python")

    # 1. Create venv if it doesn't exist
    if not os.path.exists(vpython):
        print("Creating virtual environment...")
        try:
            # Try to create venv with pip
            subprocess.run([sys.executable, "-m", "venv", "venv", "--with-pip"], check=True)
        except subprocess.CalledProcessError:
            print("Error: Failed to create virtual environment.")
            print("If you are on Linux, you might need to install the venv package.")
            print("e.g., sudo apt install python3-venv")
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        # Verify pip exists
        pip_exists = False
        try:
            subprocess.run([vpython, "-m", "pip", "--version"], capture_output=True, check=True)
            pip_exists = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Pip not found in venv. Attempting to install it via ensurepip...")
            try:
                subprocess.run([vpython, "-m", "ensurepip", "--upgrade"], check=True)
                pip_exists = True
            except subprocess.CalledProcessError:
                print("Error: pip is missing and ensurepip failed.")
                print("Please install pip manually or ensure your Python installation includes it.")
                input("\nPress Enter to exit...")
                sys.exit(1)

        # Install necessary packages
        print("Installing dependencies...")
        try:
            subprocess.run([vpython, "-m", "pip", "install", "PyYAML", "GitPython"], check=True)
        except subprocess.CalledProcessError:
            print("Error: Failed to install dependencies.")
            input("\nPress Enter to exit...")
            sys.exit(1)

    # 2. Relaunch using the venv Python if not already in it
    if os.path.abspath(sys.executable) != os.path.abspath(vpython):
        print("Switching to virtual environment...")
        completed = subprocess.run([vpython, script_path, *sys.argv[1:]])
        sys.exit(completed.returncode)

def in_venv():
    return (
        hasattr(sys, 'real_prefix') or
        sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    )

if __name__ == "__main__":
    if not in_venv():
        setup_venv()
    
    # After relaunch, we are in the venv
    try:
        import yaml
        from git import Repo, GitCommandError
    except ImportError:
        # This shouldn't happen if setup_venv worked, but for safety:
        print("Required packages not found. Attempting to install...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "PyYAML", "GitPython"], check=True)
        except subprocess.CalledProcessError:
             # If pip is missing here, we try ensurepip
             subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=True)
             subprocess.run([sys.executable, "-m", "pip", "install", "PyYAML", "GitPython"], check=True)
        
        import yaml
        from git import Repo, GitCommandError
    
    # Avoid linting errors for 'git' by using it after local import
    _ = Repo
    _ = GitCommandError

    CONFIG_FILE = "config.yml"

    def load_config():
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_config(config):
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f)

    def wait_and_exit(code=0):
        input("\nPress Enter to exit...")
        sys.exit(code)

    config = load_config()

    if "github_token" not in config:
        print("\n" + "="*50)
        print("GitHub Access Token not found.")
        print("Please generate a Personal Access Token (classic) with 'repo' scope at:")
        print("https://github.com/settings/tokens")
        print("="*50 + "\n")
        token = input("Enter your GitHub token: ").strip()
        if token:
            config["github_token"] = token
            save_config(config)
            print("Token saved to config.yml")
            # Set permissions to read/write for user only
            if os.name != "nt":
                os.chmod(CONFIG_FILE, 0o600)
        else:
            print("No token provided. Exiting.")
            wait_and_exit(1)

    github_token = config["github_token"]

    try:
        repo = Repo(".")
    except Exception as e:
        print(f"Error: Current directory is not a git repository. {e}")
        wait_and_exit(1)

    # Always pull before doing anything to avoid conflicts
    print("Pulling latest changes from GitHub...")
    try:
        remote = repo.remote(name="origin")
        url = remote.url
        if url.startswith("https://") and github_token not in url:
            auth_url = url.replace("https://", f"https://{github_token}@")
        else:
            auth_url = url
            
        with remote.config_writer as writer:
            writer.set("url", auth_url)
        try:
            remote.pull(repo.active_branch.name)
        finally:
            with remote.config_writer as writer:
                writer.set("url", url)
        print("Pull successful.")
    except GitCommandError as e:
        print(f"Warning: Could not pull latest changes. {e}")
        # Continue anyway, push will fail if there are conflicts

    if repo.is_dirty(untracked_files=True):
        print("Changes detected in the repository.")
        
        # Check if changes are in 'pack' folder
        changed_files = [item.a_path for item in repo.index.diff(None)] + repo.untracked_files
        pack_changes = [f for f in changed_files if f.startswith("pack/")]

        if not pack_changes:
            print("No changes detected in 'pack/' folder. Nothing to push.")
            wait_and_exit(0)

        print(f"Changes found in 'pack/': {len(pack_changes)} files.")
        
        commit_message = input("Enter commit message (default: 'Update resource pack'): ").strip()
        if not commit_message:
            commit_message = "Update resource pack"

        try:
            # Add only the pack folder
            repo.git.add("pack/")
            repo.index.commit(commit_message)
            print("Changes committed.")

            # Prepare for push with token
            remote = repo.remote(name="origin")
            url = remote.url
            
            # Reconstruct URL with token for authentication if it's HTTPS
            if url.startswith("https://") and github_token not in url:
                # https://github.com/user/repo.git -> https://token@github.com/user/repo.git
                auth_url = url.replace("https://", f"https://{github_token}@")
            else:
                auth_url = url # Likely SSH or already has token, assume setup is correct

            print("Pushing to GitHub...")
            # Use the authenticated URL for the push
            with remote.config_writer as writer:
                writer.set("url", auth_url)
            
            try:
                remote.push(refspec=f"{repo.active_branch.name}:{repo.active_branch.name}")
                print("Successfully pushed changes!")
            finally:
                # Restore the original URL to avoid saving the token in .git/config if possible
                # (though it might be safer to keep it if the user wants it simplified)
                # Actually, the user wants it simplified, but saving token in .git/config is a security risk.
                # However, we are already saving it in config.yml.
                with remote.config_writer as writer:
                    writer.set("url", url)

        except GitCommandError as e:
            print(f"Git error: {e}")
            wait_and_exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            wait_and_exit(1)
    else:
        print("No changes detected.")

    wait_and_exit(0)
