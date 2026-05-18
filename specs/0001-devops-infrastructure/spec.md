# Spec: DevOps Infrastructure & API Gateway

**Feature ID:** 0001-devops-infrastructure  
**Owner:** Person #1 (DevOps)  
**Status:** Approved

---

## User story

As an operator of the NanoBank system, I need a single Docker Compose command
(`make up`) to bring the entire stack online — all five application services,
their dedicated databases, the message broker, and the API gateway — so that
developers can run the full system locally and CI can validate integration.

## Context

The five services (auth, core\_banking, history, bankmarket, and an Nginx
gateway) were individually scaffolded by their respective owners. What is
missing is the glue that assembles them into one coherent, runnable system:
a unified `docker-compose.yml`, an Nginx gateway that routes and load-balances
across them, proper Dockerfiles that work from the monorepo root, and a CI
pipeline that gates every PR.

## Acceptance criteria

1. `make up` brings all services, databases, RabbitMQ, and Nginx up cleanly
   from a cold start (no pre-existing volumes).
2. `make down` tears everything down.
3. `make logs SVC=<name>` streams logs for a named service.
4. All requests enter the system via Nginx on port **8080**; direct service
   ports (8001–8005) are exposed only for local debugging.
5. Auth Service runs as **two replicas** (`auth_1`, `auth_2`) behind a
   `least_conn` upstream in Nginx.
6. Failover: stopping `auth_1` while logged in leaves the session intact
   (session is in Redis, not in-process).
7. MongoDB runs as a **replica set** (`rs0`) with 1 primary + 2 secondaries.
   An init container performs `rs.initiate()` automatically.
8. GitHub Actions runs on every push and PR:
   - ruff lint check
   - pyright type check
   - unit/integration tests
   - Docker image build smoke-check

## Out of scope

- Production TLS / certificates — local dev only.
- Image push to a registry (out of scope for the course; can be added later).
- Kubernetes / Helm manifests.
- Secrets management beyond `.env` files.
