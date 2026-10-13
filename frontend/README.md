# FastAPI Project - Frontend

The frontend is built with [Vite](https://vitejs.dev/), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [TanStack Query](https://tanstack.com/query), [TanStack Router](https://tanstack.com/router), [Tailwind CSS](https://tailwindcss.com/), and [shadcn/ui](https://ui.shadcn.com/).

## Requirements

- [Bun](https://bun.sh/)

## Quick Start

From the project root, install the dependencies and start the frontend development server:

```bash
bun install
bun run dev
```

Then open <http://localhost:5173/> in your browser.

Run `uv run bash scripts/prestart.sh` and `uv run fastapi dev` from the `backend` directory, with PostgreSQL running in Docker Compose. See [../development.md](../development.md) for the complete setup.

To serve the frontend with FastAPI, run `bun run build` from the `frontend` directory and open `http://localhost:8000`.

Check `frontend/package.json` to see the other available commands.

## KDS Design System

This frontend is a client-rendered React SPA, not a Next.js app. Vite bundles it and TanStack Router handles navigation in the browser. The repository uses Bun workspaces (`frontend` and `packages/*`); Turborepo is not required.

- `packages/ui` is the shared `@kds/ui` workspace package, migrated from `millie-ai-boilerplate`.
- Open <http://localhost:5173/kds> for all 61 component specimens. This public route does not require login or a running API.
- Gallery code lives in `src/components/kds`; the route is `src/routes/kds.tsx`. Charts and the carousel are lazy-loaded with React Suspense.
- `src/index.css` imports `@kds/ui/globals.css` once. It supplies KDS tokens to both the gallery and the existing application. The existing `src/components/ui` components retain their APIs and use the shared semantic colors.
- Pretendard fonts and their SIL Open Font License are in `public/fonts`.
- The existing theme provider owns `vite-ui-theme` storage and synchronizes both the HTML `light`/`dark` class and KDS `data-mode`. Do not add a second theme provider.

Use shared components directly:

```tsx
import { Button } from "@kds/ui/components/button"

export function SaveAction() {
  return <Button>Save</Button>
}
```

For tooltips, wrap the consuming subtree in `TooltipProvider` from `@kds/ui/components/tooltip`, as the gallery route does. KDS components use Base UI; existing local components use Radix, so their compound-component APIs are not interchangeable.

From the repository root:

```bash
bun run build
bun run typecheck
```

The typecheck command checks the frontend (including existing test files) and the complete shared UI package. Keep `packages` in the Docker build context: both frontend build images need workspace sources to resolve `@kds/ui`.

If Bun is not installed but Node.js/npm is available, use `npm exec --yes --package=bun -- bun install` and `npm exec --yes --package=bun -- bun run dev`. This runs Bun without changing the project's package manager or creating an npm lockfile.

## Removing the Frontend

If you are developing an API-only app and want to remove the frontend, you can do it easily:

* Remove the `./frontend` directory.

* In the `backend/app/main.py` file, remove the `app.frontend()` call.

* In the `backend/Dockerfile` file, remove the frontend build stage and the `COPY --from=frontend-build` instruction.

* In the `compose.override.yml` file, remove the `playwright` service.

* In the `.github/workflows/deploy.yml` file, remove the **Set up Bun**, **Install frontend dependencies**, and **Build frontend** steps.

* In the `.fastapicloudignore` file, remove the `!backend/app/frontend/` entry.

Done, you now have an API-only app. 🤓

## Generate Client

### Automatically

* From the project root, run the script:

```bash
bash ./scripts/generate-client.sh
```

* Commit the changes.

### Manually

* Make sure the backend is running.

* Download the OpenAPI JSON file from `http://localhost:8000/api/v1/openapi.json` and copy it to a new file `openapi.json` at the root of the `frontend` directory.

* To generate the frontend client, run:

```bash
bun run generate-client
```

* Commit the changes.

Regenerate the client whenever backend changes affect the OpenAPI schema.

## Using a Remote API

By default, the built frontend uses the same origin as the FastAPI app. If you want to use a remote API while running the Vite development server, you can set the environment variable `VITE_API_URL` to the URL of the remote API. For example, you can set it in the `frontend/.env` file:

```env
VITE_API_URL=https://my-domain.example.com
```

Then, when you run the frontend, it will use that URL as the base URL for the API.

## Code Structure

The frontend code is structured as follows:

* `frontend/src` - The main frontend code.
* `frontend/public` - Static assets.
* `frontend/src/client` - The generated OpenAPI client.
* `frontend/src/components` - The components of the frontend, including the shadcn/ui components in `frontend/src/components/ui`.
* `frontend/src/hooks` - Custom hooks.
* `frontend/src/lib` - Shared frontend utilities.
* `frontend/src/routes` - The frontend routes and pages.

## End-to-End Testing with Playwright

The frontend includes initial end-to-end tests using Playwright. To run the tests, you need to have the Docker Compose stack running. Start the stack with the following command:

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose up -d --wait backend
```

Then, you can run the tests with the following command:

```bash
bunx playwright test
```

You can also run your tests in UI mode to see the browser and interact with it running:

```bash
bunx playwright test --ui
```

To stop and remove the Docker Compose stack and clean the data created in tests, use the following command:

```bash
docker compose down -v
```

To update the tests, navigate to the tests directory and modify the existing test files or add new ones as needed.

For more information on writing and running Playwright tests, refer to the official [Playwright documentation](https://playwright.dev/docs/intro).
