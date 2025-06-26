#!/usr/bin/env python3
"""
Claude Desktop installation script for Minerva.
This script ensures proper installation without manual configuration fixes.
"""

import subprocess
import sys
from pathlib import Path
import json


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.absolute()


def update_env_file():
    """Update .env file with correct PYTHONPATH."""
    project_root = get_project_root()
    env_file = project_root / ".env"

    if not env_file.exists():
        print("❌ .env file not found. Please copy .env.example to .env first.")
        return False

    # Read current .env content
    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Update PYTHONPATH line
    updated_lines = []
    pythonpath_updated = False

    for line in lines:
        if line.startswith("PYTHONPATH="):
            updated_lines.append(f"PYTHONPATH={project_root / 'src'}\n")
            pythonpath_updated = True
        else:
            updated_lines.append(line)

    # Add PYTHONPATH if not found
    if not pythonpath_updated:
        updated_lines.append(f"PYTHONPATH={project_root / 'src'}\n")

    # Write updated content
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"✅ Updated .env file with PYTHONPATH={project_root / 'src'}")
    return True


def install_dependencies():
    """Install Minerva in editable mode."""
    print("📦 Installing Minerva in editable mode...")
    try:
        subprocess.run(
            ["uv", "pip", "install", "-e", ".[vector]"],
            check=True,
            cwd=get_project_root(),
        )

        subprocess.run(
            ["uv", "sync", "--extra", "vector"], check=True, cwd=get_project_root()
        )

        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def install_mcp_server():
    """Install MCP server with proper configuration."""
    project_root = get_project_root()
    print("🔧 Installing MCP server to Claude Desktop...")

    try:
        subprocess.run(
            [
                "uv",
                "run",
                "mcp",
                "install",
                "src/minerva/server.py:mcp",
                "--with-editable",
                str(project_root),
                "-f",
                ".env",
                "--name",
                "minerva",
            ],
            check=True,
            cwd=project_root,
        )

        print("✅ MCP server installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install MCP server: {e}")
        return False


def fix_claude_config():
    """Fix Claude Desktop configuration if needed."""
    config_path = (
        Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    )

    if not config_path.exists():
        print("❌ Claude Desktop config file not found")
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "mcpServers" not in config or "minerva" not in config["mcpServers"]:
            print("❌ Minerva not found in Claude Desktop config")
            return False

        minerva_config = config["mcpServers"]["minerva"]
        project_root = get_project_root()

        # Update PYTHONPATH in env
        if "env" in minerva_config:
            minerva_config["env"]["PYTHONPATH"] = str(project_root / "src")

        # Write updated config
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print("✅ Claude Desktop configuration updated")
        return True

    except Exception as e:
        print(f"❌ Failed to update Claude Desktop config: {e}")
        return False


def main():
    """Main installation function."""
    print("🚀 Starting Minerva installation for Claude Desktop...\n")

    # Step 1: Update .env file
    if not update_env_file():
        sys.exit(1)

    # Step 2: Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Step 3: Install MCP server
    if not install_mcp_server():
        sys.exit(1)

    # Step 4: Fix Claude configuration
    if not fix_claude_config():
        sys.exit(1)

    print("\n🎉 Installation completed successfully!")
    print("📝 Please restart Claude Desktop to use Minerva.")


if __name__ == "__main__":
    main()
