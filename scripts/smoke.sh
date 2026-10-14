#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Independent of asynchronous startup seeding; this checks the actual index path.
indexed=false
for attempt in {1..30}; do
  if docker compose exec -T api python scripts/ingest.py --all --data-dir /data; then
    indexed=true
    break
  fi
  sleep 2
done
if [ "$indexed" != true ]; then
  printf 'Indexing did not complete within the retry budget.\n' >&2
  exit 1
fi
curl --fail --silent http://localhost/api/v1/ready >/dev/null
curl --fail --silent http://localhost/api/v1/knowledge-bases | python3 -c 'import json,sys; assert len(json.load(sys.stdin)) > 0'
curl --fail --silent -X POST http://localhost/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"How long is the new workspace trial?","knowledge_base":"product_docs"}' \
  | python3 -c 'import json,sys; result=json.load(sys.stdin); assert result["session_id"] and result["answer"] and result["trace"]["iterations"] > 0'
printf 'Container migration, index, readiness, proxy and chat checks passed.\n'
