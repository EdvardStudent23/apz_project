# 🎬 NanoBank Project Defence Demo Guide

A complete guide to demonstrating your microservices-based digital banking system.

## 📍 Quick Access

- **Web UI**: `http://localhost:8080` (React SPA — register → login → dashboard → transfer → history)
- **Web app docs**: `web/README.md`
- **Legacy single-page demo** (kept for reference): `docs/legacy/web-demo/`
- **Demo Script (legacy)**: `docs/legacy/web-demo/DEMO_SCRIPT.md`
- **Quick Reference (legacy)**: `docs/legacy/web-demo/QUICK_REFERENCE.md`

---

## 🚀 Getting Started (5 minutes before presentation)

### 1. Start the Stack
```bash
cd /home/bubuntu/CLionProjects/apz_project
make up
```

Wait for all services to show green health dots (1-2 minutes).

### 2. Verify UI is Accessible
Open browser: `http://localhost:8080`

You should see:
- 🏦 NanoBank header
- 4 service health indicators (may show gray initially, turn green after ~10 seconds)
- 5 workflow steps
- User Management panel on left
- Account Management panel on right

### 3. Check Service Status
```bash
docker-compose ps
```

All services should show "Up" status. If any show "Exit", restart them:
```bash
docker-compose restart auth_1 auth_2 core_banking history bankmarket
```

---

## 📋 Demo Structure (10-15 minutes)

### **Section 1: Introduction (1 minute)**
- Welcome & introduce the project
- Point to the 4 service indicators showing live status
- Explain: "We're demonstrating a real microservices architecture running in Docker"

### **Section 2: Authentication & Sessions (2 minutes)**
- Register a new user
- Show the registration request/response in API Inspector
- Login with those credentials
- Point out the JWT token

**Key talking points**:
- Argon2id password hashing
- JWT token generation
- Redis session storage enables replica failover
- Nginx load-balances across 2 replicas

### **Section 3: Account Management (1.5 minutes)**
- Create 3 accounts (USD, EUR, UAH)
- Show them in the account list with balances
- Explain PostgreSQL storage

**Key talking points**:
- Each service owns its database (no shared schema)
- Independent deployability
- Initial balance of 1000 per account

### **Section 4: ACID Transfer (3 minutes)** ⭐ **MOST IMPORTANT**
- Transfer 100 USD to EUR account
- Watch the API Inspector
- Show the balance changes
- Explain the ACID guarantees

**Key talking points**:
- Transaction atomicity (all or nothing)
- Row-level locking prevents deadlocks
- Currency conversion happens atomically
- Event published to RabbitMQ after commit
- Transactional outbox pattern (no message loss)

### **Section 5: Event-Driven History (2 minutes)**
- Refresh transaction history
- Show the transaction appears
- Explain the eventual consistency

**Key talking points**:
- RabbitMQ topic exchange pattern
- History Service as async consumer
- MongoDB replica set with quorum-aware failover
- CQRS pattern (separate write and read models)
- Eventual consistency is acceptable here

### **Section 6: Architecture Overview (2 minutes)**
- Explain the 3-tier per service:
  1. **Routes** (HTTP) → `/auth/register`, `/accounts`, `/transfers`, `/history`
  2. **Services** (Business Logic) → Authentication, Account management, Transfer logic
  3. **Database** (Persistence) → PostgreSQL, Redis, MongoDB, Neo4j

- Point to the data flow:
  ```
  UI → Nginx Gateway → Service Layer → Database
  ```

### **Q&A & Closing (1-2 minutes)**
- Answer questions
- Summarize key achievements
- Thank the panel

---

## 🎯 Key Points to Emphasize

### Microservices Design
✓ **5 independent services** with single responsibility  
✓ **No shared database** between services  
✓ **Independent deployability** - one service can be updated without affecting others  
✓ **Technology choice** - all happen to use Python/FastAPI, but could use different languages

### Reliability & Resilience
✓ **Replica failover** - Auth Service has 2 replicas, load-balanced by Nginx  
✓ **Session persistence** - Redis ensures session survives replica failure  
✓ **Quorum-aware failover** - MongoDB automatically goes read-only if quorum is lost  
✓ **Circuit breaking** - Nginx can detect dead replicas and route around them

### Financial Correctness (ACID)
✓ **Transactional integrity** - Money can't disappear or be duplicated  
✓ **Row-level locking** - Prevents race conditions  
✓ **Deterministic lock ordering** - Prevents deadlocks  
✓ **Atomic currency conversion** - Conversion happens inside transaction  

### Event-Driven Architecture
✓ **Asynchronous processing** - History updates don't block transfer  
✓ **Message durability** - RabbitMQ persists events if consumer is down  
✓ **Idempotent processing** - Same event can be processed multiple times safely  
✓ **Distributed tracing** - x-request-id header follows request through all services  

### Production-Ready Patterns
✓ **Transactional outbox** - Events only published if database commit succeeds  
✓ **CQRS** - Command (transfers) separate from Query (history)  
✓ **Saga pattern** - Distributed transactions without 2-phase commit  
✓ **Circuit breaker** - Implicit in Nginx health checks  

---

## 💡 How to Answer Common Questions

### "How do you handle distributed transactions?"
> "We use the Saga pattern. The transfer is atomic *within* Core Banking (ACID). The event publication to RabbitMQ is transactional (outbox pattern). The History Service consumer is idempotent, so if an event is reprocessed, it doesn't create duplicates. Together, this gives strong guarantees without complex 2-phase commit."

### "What happens if History Service is down?"
> "The transfer completes immediately—the user gets their money transferred. The event sits in RabbitMQ's durable queue. When History Service comes back online, it processes all queued events in order. This is eventual consistency, which is acceptable for a read-only history."

### "Why not use a shared database?"
> "Shared databases create tight coupling. Each service becomes dependent on a shared schema. If you need to deploy a new version of History Service with a new column, you need to coordinate with all other services. With independent databases, History Service can change its schema without touching anyone else."

### "How does JWT validation work without hitting Auth Service every time?"
> "Auth Service exposes its public key at `/.well-known/jwks.json`. Every service fetches this key once at startup and caches it. Then they can validate JWTs locally using the public key. No per-request hop to Auth needed."

### "What if someone tries to transfer more money than they have?"
> "The transaction checks account balance inside the PostgreSQL transaction. If insufficient, it rolls back with an error. No debit occurs. This is enforced at the database level, not just in application code."

### "Can you show me the code?"
> Point them to:
> - Core Banking: `services/core_banking/src/services/transfer.py`
> - Auth: `services/auth/src/services/user_service.py`  
> - History: `services/history/src/services/consumer.py`
> - Common patterns: `CLAUDE.md` (engineering spec)

---

## 📊 Before/After Demo

### Before Starting the Demo
- Terminal showing: `docker-compose ps` (all services "Up")
- Browser with 2 tabs open:
  - Tab 1: `http://localhost:8080` (the dashboard)
  - Tab 2: DevTools (F12) on the Network tab
- Secondary monitor or screen share ready

### During the Demo
- Focus on browser with dashboard
- Use secondary monitor for terminal/slides if needed
- Keep DevTools visible to show actual HTTP requests

### After the Demo
- Have docs ready to share
- Keep the stack running for Q&A
- Be prepared to restart services if they ask to see failover

---

## 🎓 Learning Resources to Reference

**For the panel/audience**:
- `docs/architecture.md` - System design and component diagram
- `docs/vision.md` - Product vision and requirements
- `docs/use-cases.md` - User stories that drove the design
- `docs/events.md` - Event schemas (TransactionCreatedEvent, etc)
- `CLAUDE.md` - Complete engineering specification

**For failover verification**:
- `docs/runbooks/failover-verification.md` - How to test Auth replica failover
- `docs/runbooks/mongo-quorum.md` - How to test MongoDB quorum loss

**In the code**:
- Services are in `services/auth`, `services/core_banking`, `services/history`, `services/bankmarket`
- Each has its own migrations in `services/*/migrations/`
- Shared patterns in `libs/` (common, logging, messaging, auth_client)

---

## ⚠️ Potential Issues & Quick Fixes

| Issue | Fix |
|-------|-----|
| Service shows gray dot | Wait 10 seconds, or restart: `docker-compose restart SERVICE` |
| 422 error on register | Password must have letters, numbers, special chars |
| UI won't load | Check `docker-compose logs nginx` or refresh browser |
| Transfer shows 400 | Make sure accounts are different and balance is sufficient |
| History shows "No transactions" | Wait 2-3 seconds and refresh (eventual consistency) |
| All services show gray | Run `docker-compose up -d` and wait for health checks |

---

## 🎬 Recording/Presentation Tips

### For Screen Recording
1. **Set resolution**: 1920×1080 or higher
2. **Zoom browser**: 125-150% for readability
3. **Use presentation mode**: F11 (Firefox/Chrome fullscreen)
4. **Slow down**: Explain each step clearly, pause between sections
5. **Show the code**: Close up on key files (transfer logic, outbox pattern, etc)
6. **Annotate**: Use a drawing app to highlight key elements

### For Live Demo
1. **Test beforehand**: Run the demo once fully before presentation
2. **Pre-create data**: Have test accounts ready to save time
3. **Keep calm**: If something fails, explain what should have happened
4. **Show the logs**: `docker-compose logs SERVICE_NAME` if something seems wrong
5. **Be confident**: You built this, you understand it better than anyone

### For Panel Discussion
1. **Memorize the architecture**: Know it by heart
2. **Know the tradeoffs**: Eventual consistency vs ACID, monolith vs microservices
3. **Have numbers ready**: ~5 microservices, ~4 databases, ~1000s of possible users
4. **Reference the brief**: Point to CLAUDE.md for the original requirements
5. **Admit unknowns**: "Great question, we could explore that in future work"

---

## ✅ Pre-Presentation Checklist

- [ ] Docker Desktop is running
- [ ] Terminal access to `/home/bubuntu/CLionProjects/apz_project`
- [ ] Browser pointing to `http://localhost:8080`
- [ ] All 4 service indicators showing green (or about to)
- [ ] DevTools open with Network tab visible
- [ ] Demo script printed or visible: `web/DEMO_SCRIPT.md`
- [ ] Quick reference card handy: `web/QUICK_REFERENCE.md`
- [ ] Secondary monitor/screen share working (if needed)
- [ ] Clean desktop (no confidential files visible)
- [ ] Volume turned down (browser alerts might be loud)

---

## 🎯 Success Criteria

By the end of the demo, the panel should understand:

1. **What**: A microservices digital bank with ACID transfers
2. **Why**: Demonstrates real banking requirements + distributed system challenges
3. **How**: 5 independent services, async messaging, eventual consistency
4. **Tech**: Python/FastAPI, PostgreSQL, MongoDB, Redis, RabbitMQ, Docker
5. **Resilience**: Replica failover, quorum awareness, event durability

---

## 📞 Support

If something goes wrong during the demo:

1. **Check the logs**: `docker-compose logs SERVICE_NAME`
2. **Restart the service**: `docker-compose restart SERVICE_NAME`
3. **Restart the stack**: `docker-compose down && docker-compose up -d`
4. **Check the docs**: `CLAUDE.md` has all the design decisions

You've got this! 🚀

---

**Created**: 2026-05-19  
**Last Updated**: 2026-05-19  
**For**: NanoBank Microservices Course Project Defence
