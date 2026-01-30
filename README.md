# Resource Pack Publisher

This tool automatically synchronizes your local `pack/` folder with a GitHub repository. It also triggers GitHub Actions to zip and publish the resource pack.

## How to use

1.  Place your resource pack files in the `pack/` folder.
2.  Run the synchronization script:
    ```bash
    python update-pack.py
    ```
    *The script will automatically create a virtual environment and install all necessary dependencies on its first run.*
3.  The script will:
    *   Set up a virtual environment and install dependencies (`PyYAML`, `GitPython`).
    *   Ask for your GitHub Personal Access Token (on first run).
    *   Pull latest changes from GitHub.
    *   Commit any changes in the `pack/` folder.
    *   Push the changes to GitHub.
    *   Wait for you to press Enter before closing the window (useful for double-click runs).

## Configuration

The script stores its configuration (including your GitHub token) in `config.yml`. Do not share this file.

## GitHub Action

Ensure your repository has a GitHub Action set up to zip the `pack` folder and host it (e.g., via GitHub Pages).
