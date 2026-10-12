# SmartBase Online Bookstore

A starter project for an online bookstore, built with a React frontend and a
Flask backend. The local development environment uses Docker Compose, with a
MySQL service available for future development.

## Developer setup

### Prerequisites

- Docker Desktop (with WSL 2 integration on Windows) or Docker Engine
- Visual Studio Code
- The **Dev Containers** extension for VS Code (`ms-vscode-remote.remote-containers`)
- Git

On Windows, install and update WSL 2 if needed. From an Administrator PowerShell
terminal, run:

```powershell
wsl --install -d Ubuntu
wsl --update
```

### Open the development container

1. Clone this repository and open its folder in VS Code.
2. Install the Dev Containers extension if it is not already installed.
3. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and select
   **Dev Containers: Reopen in Container**.
4. Wait for the container to build. Docker Compose starts the app development
   container and the MySQL 8 database; the container configuration also adds
   the development command aliases to Bash.
5. Open a **new Bash terminal** in the container so the aliases are available.

The dev container is based on Python 3.11 and installs Node.js 20 and MySQL
client tools. The first build may take a few minutes.

### Run the app

From a Bash terminal in the repository root, run:

```bash
devup
```

This creates the backend virtual environment if needed, installs backend Python
packages only when they are missing, starts Flask, installs frontend packages
if Vite is missing, and starts the Vite development server. The first run may
take a few minutes while dependencies are downloaded; later starts skip those
install steps. Open:

- Frontend: <http://localhost:5173>
- Backend health check: <http://localhost:5000/api/health>

Press `Ctrl+C` in the terminal to stop the Vite server. The helper script then
stops the Flask process it started. The Compose-managed MySQL service remains
running until you stop the Compose environment.

If the aliases are not available, run the script directly:

```bash
bash scripts/dev-tasks.sh up
```

### Development commands

| Command | Description |
| --- | --- |
| `devup` | Install missing dependencies and start the Flask and Vite development servers. |
| `devcheck` | Attempt backend unit-test discovery and run the frontend ESLint command. |
| `devclean` | Remove Python caches, the frontend `node_modules` directory, and the backend virtual environment. Dependencies are installed again on the next `devup`. |

The aliases are added to `~/.bashrc` when the Dev Container is created. The
check script currently ignores failures from both checks, so `devcheck` may
report completion even if a test or lint command fails.

To stop the Docker Compose services when finished, run from the repository
root:

```bash
docker compose down
```

## Project structure

```text
.
├── .devcontainer/       # VS Code development container configuration
├── backend/             # Flask API
├── frontend/            # React application built with Vite
├── scripts/             # Development helper script
└── docker-compose.yml   # App and MySQL services
```

## Technology

- **Frontend:** React and Vite
- **Backend:** Python and Flask
- **Database service:** MySQL 8
- **Development environment:** Docker Compose and VS Code Dev Containers

The current app is intentionally a starter: the frontend displays sample books,
and the Flask backend currently provides a health-check endpoint. MySQL is
included in the development environment but is not yet used by the app.
