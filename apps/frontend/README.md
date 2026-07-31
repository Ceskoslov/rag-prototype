# Universal RAG frontend

React 19 and Vite 8 client for the Universal RAG API.

The knowledge-base selector is populated dynamically from
`GET /api/v1/knowledge-bases`. Selecting “All knowledge bases” omits the
optional filter and lets the backend search every indexed collection. Answers
show source documents and a domain-neutral RAG execution trace.

```bash
npm ci
npm run dev
```

Quality checks:

```bash
npm run lint
npm test
npm run build
```

Set `VITE_API_URL` in `.env` when the API is not available at `/api`.
