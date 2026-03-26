# NanoBank – API Gateway & DevOps

> **Person #1** owns this layer: Nginx entry-point, Docker Compose orchestration, GitHub Actions CI/CD.

---

## Repository layout (your part)

```
├── nginx/
│   ├── Dockerfile          # Nginx image
│   └── nginx.conf          # Routing + JWT auth_request + HA upstream
├── docker-compose.yml      # Full system: all 5 services + all DBs
├── .github/
│   └── workflows/
│       └── ci-cd.yml       # Build & push images on push to main
├── .env.example            # Template – copy to .env locally
└── .gitignore
```

---

## How it all works

### Nginx routing table

| External path | Upstream | JWT required? |
|---|---|---|
| `GET /health` | nginx (inline) | ✗ |
| `/auth/*` | `auth_service` upstream (load-balanced ×2) | ✗ |
| `/banking/*` | `core-banking-service` | ✓ |
| `/history/*` | `history-service` | ✓ |
| `/market/*` | `bank-market-service` | ✓ |

Protected routes use Nginx's `auth_request` module: every request is forwarded internally to `auth-service/validate`. If the Auth Service returns **200** the request continues and the decoded `X-User-ID` header is forwarded downstream. Any other status code returns a JSON 401.

### High Availability – Auth Service

Two identical instances (`auth-service-1`, `auth-service-2`) sit behind an Nginx `upstream` block configured with `least_conn` load balancing. Both share the same PostgreSQL database and the same Redis session store. If one instance dies, Nginx's `max_fails=3 fail_timeout=10s` marks it as unavailable and routes all traffic to the surviving instance — users stay logged in because their sessions live in Redis, not in process memory.

### MongoDB Replica Set

The `mongo-init` one-shot container calls `rs.initiate()` to form a 3-node replica set (`rs0`): one Primary with `priority: 2` and two Secondaries. Kill the primary container and MongoDB automatically elects a new one within ~10 seconds.

---

## Local setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-org>/nanobank.git
cd nanobank

# 2. Create your local .env
cp .env.example .env
# Edit .env and set JWT_SECRET and NEO4J_PASSWORD

# 3. Build and start everything
docker compose up --build

# 4. Check the gateway
curl http://localhost/health
# → {"status":"ok","service":"api-gateway"}

# 5. Try a protected route without a token
curl http://localhost/banking/
# → {"error":"Unauthorized","message":"Valid JWT token is required"}

# 6. RabbitMQ management UI
open http://localhost:15672   # user: nanobank / pass: nanobank

# 7. Neo4j browser
open http://localhost:7474
```

---

## Demonstrating HA for the exam

### Kill one Auth Service instance
```bash
docker stop auth-service-1
# All /auth/* requests now go to auth-service-2
# Already-logged-in users stay authenticated (session in Redis)
docker start auth-service-1   # bring it back
```

### Kill MongoDB Primary
```bash
docker stop mongo-primary
# Wait ~10 s for election
docker exec mongo-secondary1 mongosh --eval "rs.status()"
# One of the secondaries is now PRIMARY
docker start mongo-primary    # rejoins as secondary
```

---

## CI/CD (GitHub Actions)

| Trigger | What happens |
|---|---|
| Push to `main` | Validate compose → Build all 5 images → Push to GHCR with `latest` + `sha-<short>` tags |
| Pull Request | Validate → Build → Spin up full stack → Smoke-test `/health` (200) and `/banking/` without JWT (401) → Tear down |

Images are published to `ghcr.io/<owner>/nanobank/<service>:latest`.
