# lovely-chat

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd) 
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Levantar proyecto completo en dev

```sh
make dev
```

### Levantar solo el backend

Sin `make`, puedes iniciarlo directamente con `uvicorn`:

```sh
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

Esto inicia FastAPI con `reload` en `http://127.0.0.1:8001`.

Si prefieres no activar el entorno virtual:

```sh
cd backend
.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

Con `make`, el comando equivalente es:

```sh
make dev-backend
```

### Configurar el proveedor de modelo

El backend soporta `Google`, `OpenAI` y `Ollama`. La selección se hace con variables de entorno en `backend/.env`.

Por defecto, el proyecto queda usando Gemini:

```env
MODEL_PROVIDER=google
GOOGLE_API_KEY=tu_api_key
GOOGLE_MODEL=gemini-2.5-flash-lite
```

Para usar OpenAI:

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=tu_api_key
OPENAI_MODEL=gpt-4.1-mini
```

Para usar Ollama:

```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_API_STYLE=openai
```

Targets disponibles:

```sh
make dev-backend   # FastAPI con reload en http://127.0.0.1:8001
make dev-frontend  # Vite en http://127.0.0.1:5173
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Run Headed Component Tests with [Cypress Component Testing](https://on.cypress.io/component)

```sh
npm run test:unit:dev # or `npm run test:unit` for headless testing
```

### Run End-to-End Tests with [Cypress](https://www.cypress.io/)

```sh
npm run test:e2e:dev
```

This runs the end-to-end tests against the Vite development server.
It is much faster than the production build.

But it's still recommended to test the production build with `test:e2e` before deploying (e.g. in CI environments):

```sh
npm run build
npm run test:e2e
```
