# Free deployment options

Free-tier terms change frequently. The recommendations below were checked on
2026-07-31.

## Recommended: Oracle Cloud Always Free VM

This is the closest fit for the repository without redesigning its storage
layer. An Always Free Ampere A1 allocation can provide up to 2 OCPUs and 12 GB
of memory, enough for the API, frontend, PostgreSQL, Redis, Chroma, and the
default local embedding model on one ARM64 VM.

Deploy the existing Docker Compose stack on Ubuntu ARM64, restrict database
ports to the Docker network, and expose only ports 80/443 through Nginx.

Advantages:

- No application split or managed-service adapters.
- Persistent block storage for PostgreSQL, Redis, and Chroma.
- Enough memory for local multilingual embeddings.
- Always Free resources do not expire while the account and allocation remain
  eligible.

Limitations:

- Registration and payment-card verification are usually required.
- Always Free capacity can be unavailable in a chosen home region.
- This is a single-host deployment; configure backups and monitoring.

Official references:

- <https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm>
- <https://www.oracle.com/cloud/free/faq/>

## Selected demo deployment: Render plus managed free services

Use a Render Free web service for FastAPI and a free static site for the React
frontend. Externalize state to Neon Postgres and Upstash Redis. Chroma Cloud's
Starter plan has no monthly base fee and includes initial credits, but it is
usage-priced after those credits.

This option needs a deployment adapter for Chroma Cloud and should use hosted
embeddings or a much smaller local model because Render Free web services have
tight memory limits.

The adapter and Blueprint are included in this repository. Follow
[`render-deployment.md`](render-deployment.md).

Important free-tier limitations:

- Render web services sleep after inactivity and have an ephemeral filesystem.
- Render's own Free Postgres expires after 30 days, so Neon is preferable.
- Render Free Key Value is in-memory; Upstash is preferable for persistent
  parent chunks.
- Hosted LLM and embedding API calls are not generally free.

Official references:

- <https://render.com/docs/free>
- <https://neon.com/pricing>
- <https://upstash.com/pricing/redis>
- <https://www.trychroma.com/pricing>

## Serverless alternative: Google Cloud Run

Cloud Run includes a monthly free usage allowance and scales to zero. Pair it
with Neon, Upstash, and Chroma Cloud. It is a better scaling path than a free
single VM but requires a billing account, uses several external services, and
can incur charges beyond the free allowances.

Official reference:

- <https://cloud.google.com/run/pricing>

## Recommendation

For a portfolio or low-traffic demo that should remain genuinely close to zero
cost, use Oracle Cloud Always Free and the existing Compose stack. For the
fastest click-through demo, use Render, accepting cold starts and external
managed-service dependencies.
