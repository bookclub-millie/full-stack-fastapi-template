# FastAPI Project - Development

## Local Development

For local development, run PostgreSQL and Mailpit with Docker Compose, and run the FastAPI and Vite development servers locally.

Start the supporting services:

```bash
docker compose up -d db mailpit
```

Then, from the `backend` directory, install the dependencies and prepare the database:

```bash
uv sync
uv run bash scripts/prestart.sh
```

Start the FastAPI development server:

```bash
uv run fastapi dev
```

In another terminal, from the project root, install the frontend dependencies and start the Vite development server:

```bash
bun install
bun run dev
```

Now you can open these URLs:

Frontend development server: <http://localhost:5173>

Backend API: <http://localhost:8000>

Automatic interactive API documentation with Swagger UI: <http://localhost:8000/docs>

Mailpit: <http://localhost:8025>

The frontend development server uses the backend at `http://localhost:8000`, as configured in `frontend/.env`.

The frontend is a Vite/React CSR app in a Bun workspace, not Next.js. The shared KDS package is `packages/ui` (`@kds/ui`), alongside `packages/react-email`. Run `bun run storybook` and open <http://localhost:6006> to develop components without the backend or database. Authenticated application pages still require the backend.

Run `bun run build` and `bun run typecheck` from the repository root to check the frontend and shared UI. See [the frontend KDS guide](./frontend/README.md#kds-design-system) for imports, styles, fonts, and theme integration.

See [frontend quality commands](./frontend/README.md#frontend-quality) for component accessibility, unit tests, visual regression, and CI. `bun run lint:check` and `bun run check:deps` are read-only checks. Run Storybook separately from the application; it is not part of the production app bundle.

Code style is shared through the root `biome.json`. Run `bun run format` to apply StandardJS-like formatting and organize imports across authored frontend, package, and JS/TS script files; it does not run lint rules or tests. See [code conventions](./frontend/README.md#code-conventions) for function-expression and filename rules.

### Frontend Served by FastAPI

Build the frontend from the `frontend` directory:

```bash
bun run build
```

The build is written to `backend/app/frontend` and served by FastAPI at <http://localhost:8000>. Rebuild the frontend after making frontend changes.

## Frontend Agent Skills

Shared skill sources live in `.agents/skills/`. Matching relative symlinks in `.claude/skills/` let Claude Code use the same files without maintaining duplicate copies.

| Skill | Use |
|---|---|
| `feature-sliced-design` | Frontend architecture and dependency boundaries |
| `impeccable` | UI design guidance, review, and design tooling |
| `nextjs` | Next.js projects only; retained for future use, not the current Vite CSR frontend |
| `vercel-react-best-practices` | React performance guidance; apply Next.js/server-specific rules only to matching code |

The source files, references, and runtime assets are retained from `millie-ai-boilerplate`. `skills-lock.json` records the three upstream-managed skills; Impeccable carries its engine version in `.agents/skills/impeccable/scripts/VERSION`. OpenSpec skills and its workflow are not included.

From the repository root, inspect skill discovery and the Impeccable launcher:

```bash
npx skills list
.agents/skills/impeccable/scripts/impeccable engine-probe
.claude/skills/impeccable/scripts/impeccable --help
```

Impeccable's launcher uses a local engine or downloads the pinned engine into the user cache on first use. Initial download requires network access and verifies the release checksum. Windows without a POSIX shell uses `scripts/impeccable.cmd`. Follow each skill's `SKILL.md` for task-specific setup; copying a skill does not migrate application architecture or initialize design context.

Existing `library-skills`, FastAPI, and SQLModel integrations are preserved. Backend package-provided skill links require the Python dependencies to be installed; use the existing Library Skills instructions to check or repair those links.

## Full Stack with Docker Compose

To run the backend and built frontend in Docker Compose:

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose watch
```

Now you can open these URLs:

Application, with the frontend and API served by FastAPI: <http://localhost:8000>

Automatic interactive API documentation with Swagger UI: <http://localhost:8000/docs>

Adminer, database web administration: <http://localhost:8080>

Traefik UI, to see how the routes are being handled by the proxy: <http://localhost:8090>

Mailpit: <http://localhost:8025>

Stop a locally running FastAPI server before starting the Compose backend because both use port `8000`.

**Note**: The first time you start the stack, it might take a minute for all the services to be ready. To monitor it, use `docker compose logs`, or `docker compose logs backend` for the backend service.

## Mailpit

[Mailpit](https://mailpit.axllent.org) captures emails sent during local development instead of delivering them. The local backend connects to it at `localhost:1025`, and the Compose backend connects to the `mailpit` service. Captured emails are available at <http://localhost:8025>.

## Docker Compose Files and Environment Variables

The main `compose.yml` file contains the configuration shared by the whole stack. Docker Compose loads it automatically.

The `compose.override.yml` file adds local development settings, such as mounting the source code as a volume. Docker Compose also loads it automatically and applies it on top of `compose.yml`.

The `compose.deploy.yml` file contains the deployment-specific settings, including HTTPS and automatic certificate handling. It is explicitly combined with `compose.yml` when deploying the application.

The backend reads local settings from the `.env` file. Docker Compose also uses it for variable interpolation and passes the settings each container needs.

After changing variables, make sure you restart the stack:

```bash
docker compose watch
```

## The `.env` File

The tracked `.env` file contains local development defaults, passwords, and other configuration. Its hostnames use `localhost` for processes running on your machine. Docker Compose overrides hostnames such as the database and SMTP server with their Compose service names.

Do not store deployment secrets in `.env`. Configure them as described in the [FastAPI Cloud deployment guide](./deployment.md) or the [Docker Compose deployment guide](./deployment-docker-compose.md).

## Pre-commit Hooks and Code Linting

The project uses [prek](https://prek.j178.dev/), a modern alternative to [pre-commit](https://pre-commit.com/), for code linting and formatting.

You can find a file `.pre-commit-config.yaml` with configurations at the root of the project.

### Install `prek` to Run Automatically

`prek` is already part of the dependencies of the project.

From the project root, install the Git hook so that `prek` runs automatically before each commit:

```bash
uv run prek install -f
```

The `-f` flag forces the installation, in case there was already a `pre-commit` hook previously installed.

Now whenever you try to commit, for example with:

```bash
git commit
```

`prek` will check and format the code you are about to commit. If it modifies any files, add those files to Git again before committing.

### Run `prek` Manually

You can also run `prek` manually on all files from the project root:

```bash
uv run prek run --all-files
```
