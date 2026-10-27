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

Open the project in its Compose dev container using **Dev Containers: Reopen in
Container**. Do not separately run `docker compose up` from PowerShell first:
that can create a second Compose project/container. Once the container is open,
start the app from a Bash terminal at the repository root:

```bash
devup
```

This creates the backend virtual environment if needed, installs missing
backend and frontend packages, and starts Flask and Vite in the same Compose
container that publishes their ports. Keep the terminal running while using
the app. On an empty MySQL database, `devup` loads the schema and sample data
from `init.sql`; it does not re-import seed data into an existing database.
The first run may take a few minutes while dependencies are installed.

When Flask and Vite have started, open:

- Frontend: <http://localhost:5174>
- Backend health check: <http://localhost:5001/api/health>
- Database connection check: <http://localhost:5001/api/health/database>

Compose waits for MySQL to pass its health check before starting the app
container. The database check should then return the database status and book
count.

Press `Ctrl+C` in the terminal to stop Flask and Vite; MySQL remains available
while the Dev Container is open. Closing the Dev Container stops its Compose
services. The MySQL data volume is preserved.

After reopening the dev container, run `devup` again to start Flask and Vite.
If the alias is unavailable, run:

```bash
bash scripts/dev-tasks.sh up
```

### Development commands

| Command | Description |
| --- | --- |
| `devup` | Install missing dependencies and start Flask and Vite in the Compose app container. |
| `devcheck` | Attempt backend unit-test discovery and run the frontend ESLint command. |
| `devclean` | Remove Python caches, the frontend `node_modules` directory, and the backend virtual environment. Dependencies are installed again the next time the Compose `app` service starts. |

The `devup`, `devcheck`, and `devclean` aliases are added to `~/.bashrc` when
the Dev Container is created. The check script currently ignores failures from
both checks, so `devcheck` may report completion even if a test or lint command
fails.

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
and the Flask backend provides health checks, including a database connection
check against MySQL.
