# 🎬 NanoBank Demo Script for Project Defence

## Pre-Presentation Checklist
- [ ] Run `make up` and wait 30 seconds for services to fully initialize
- [ ] Navigate to `http://localhost:8080` in a browser
- [ ] Check that all 4 service health dots are green
- [ ] Open browser DevTools (F12) to show network tab during transfers
- [ ] Have a secondary monitor/screen share ready

## Demo Duration: ~10 minutes

---

## **1. Introduction (1 minute)**

> **What to say**: "This is NanoBank, a microservices-based digital bank demonstrating real banking primitives with ACID transfers, event-driven architecture, and distributed system resilience."

**What to show**:
- Point to the 4 service health indicators at top
- Explain: "These green dots show that all 4 services are running and healthy"
- Show the 5-step workflow visualization

---

## **2. User Registration & Authentication (2 minutes)**

> **What to say**: "Let's start by registering a new user. This hits the Auth Service which uses argon2id password hashing and stores everything in PostgreSQL."

**Step-by-step**:
1. Click on the "User Management" card (left side)
2. Enter:
   - Username: `demo_user_` + timestamp
   - Email: `demo@bankingsystem.io`
   - Password: `SecurePass123!`
3. Click **Register User**

**Wait for success** then say:
> "See the request/response in the API Inspector below? The password was hashed with argon2id before storage. Notice the JWT wasn't generated yet—that comes on login."

4. Switch to **Login** tab
5. Enter same username and password
6. Click **Login**

**When successful**:
> "Now we have a JWT token and a Redis session. Each auth service replica can validate this token independently using a public key they fetched at startup. The Redis session means even if one replica goes down, the session persists."

Show the User ID that appears.

---

## **3. Creating Bank Accounts (1.5 minutes)**

> **What to say**: "Let's create accounts in three different currencies. The Core Banking Service stores these in PostgreSQL with each account getting an initial balance of 1000 units."

**Step-by-step**:
1. Go to "Account Management" card (right side)
2. Create 3 accounts:
   - USD → Click **Create Account** (wait 2 seconds)
   - EUR → Change dropdown → Click **Create Account**
   - UAH → Change dropdown → Click **Create Account**

**While waiting**:
> "Each account creation is a simple HTTP request through the Nginx gateway. In production, the gateway load-balances across multiple service replicas."

**When all 3 are created**:
> "Notice each account has a unique ID (UUID) and the balance is 1000 in each currency. The service stored this in a Postgres database. Each service owns its own database—there's no shared schema between services."

---

## **4. ACID Money Transfer (3 minutes) ⭐ **Most Important**

> **What to say**: "Now comes the most critical part—an ACID transfer that demonstrates transactional guarantees, currency conversion, and event-driven architecture."

**Step-by-step**:
1. Go to "Money Transfer" card
2. Set:
   - From Account: USD account
   - To Account: EUR account  
   - Amount: `100.00`
3. Click **Send Transfer**

**While processing** (should take 1-2 seconds):
> "What's happening now:
> 1. The transfer goes to Core Banking Service
> 2. A PostgreSQL transaction begins
> 3. Both account rows are locked in deterministic order (smaller ID first) to prevent deadlocks
> 4. The USD amount is converted to EUR using a fixed rate
> 5. Source is debited, destination is credited
> 6. **Everything commits atomically—all or nothing**
> 7. After commit, an event is published to RabbitMQ using the **transactional outbox pattern**
> 8. The History Service's consumer picks it up and writes to MongoDB"

**When successful**:
> "Look at the API Inspector—status 200. The balance changes happened instantly in the database, but the event will eventually be consumed by the History Service."

**Point out**:
- The request shows the transfer details
- The response confirms the transaction ID
- Account balances now show the transfer

---

## **5. Eventual Consistency & Transaction History (2 minutes)**

> **What to say**: "The History Service is a consumer reading events from RabbitMQ. It demonstrates CQRS—the write model (Core Banking) and read model (History) are separate. This eventual consistency is documented and accepted."

**Step-by-step**:
1. Go to "Transaction History" card
2. Click **Refresh History**

**If you see the transaction**:
> "Perfect! The event was consumed by the History Service consumer and written to MongoDB. Notice the timestamp matches our transfer time. MongoDB is configured as a replica set with quorum-aware failover—if 2 of 3 nodes go down, it demotes to read-only automatically."

**If you don't see it yet**:
> "It can take a few seconds for the event to be consumed. This is eventual consistency in action. In real banking, you'd typically apply the debit immediately and credit after settlement. We're demonstrating both strong consistency (ACID) and weak consistency (eventual)."

Wait a few seconds and refresh again.

---

## **6. Architecture Deep Dive (1-2 minutes)**

> **What to say**: "Let's look at how all 5 services work together."

**Point to the service health indicators**:
- Auth Service (2 replicas behind Nginx load balancer)
- Core Banking (manages accounts and ACID transfers)
- History Service (reads from RabbitMQ, writes to MongoDB)
- BankMarket (would handle marketplace recommendations)

**Explain the flow**:
```
Browser → Nginx Gateway (8080) → 4 Services (8001-8005)
          ↓
    Load balances across:
    - Auth Service × 2 replicas (least_conn policy)
    - Core Banking (single for demo)
    - History (single for demo)
    - BankMarket (single for demo)
```

> "Each service has its own database. There's no shared schema. They communicate via REST APIs and RabbitMQ events. The gateway propagates JWT tokens and request IDs across service boundaries for tracing."

---

## **7. Demonstration of Failover (Optional - 2 minutes)**

> "Want to see replica failover in action?"

If you want to show this:

```bash
# In another terminal:
docker-compose stop auth_1
```

Then:
1. Try to login again on the UI
2. Point out: "Nginx automatically routes to auth_2. The session is in Redis, not in-process, so the user stays logged in."

```bash
# Bring it back:
docker-compose up auth_1 -d
```

---

## **8. Closing Remarks (30 seconds)**

> **What to say**: "This demo showed:
> ✓ **Microservices**: 5 independent services, each with a single responsibility
> ✓ **Resilience**: Replicas, load balancing, separate databases
> ✓ **ACID Guarantees**: Transactional consistency for money transfers
> ✓ **Event Sourcing**: History service as eventual consistent read model
> ✓ **Real Banking Primitives**: User accounts, balances, transfers, currency conversion
> 
> This all runs in Docker Compose, but the patterns scale to Kubernetes. Each service can be deployed, scaled, and updated independently."

---

## **Talking Points if Asked Questions**

### "Why separate databases?"
> "It prevents tight coupling. Each service owns its data contract. If History Service needs a new field, it doesn't require Core Banking changes. It's the 'database per service' pattern from microservices architecture."

### "Why RabbitMQ instead of REST?"
> "REST calls are synchronous—if History Service is down, the transfer would fail. RabbitMQ makes it asynchronous. The event is persisted to the queue, so even if History goes down for 10 minutes, it'll process all events when it comes back up."

### "What about atomicity across services?"
> "We use the **Saga Pattern** here. The transfer is atomic *within* Core Banking. The event publishing is transactional (outbox pattern) so no events are lost. History Service processing is idempotent (keyed on event_id), so retries don't create duplicates. Together, this gives us strong guarantees."

### "How does currency conversion work?"
> "Fixed rates in the code (USD/EUR/UAH). In production, you'd call an external rate API. The conversion happens *inside* the ACID transaction, so partial conversions can't happen."

### "What if the transfer fails halfway?"
> "Impossible. The PostgreSQL transaction will rollback if anything fails—insufficient funds, invalid account, etc. RabbitMQ event publishing only happens *after* commit, so events only exist for successful transfers."

---

## **Recording Tips**

If recording the demo:
- Use a 2560×1440 screen at 60fps
- Open DevTools to show network requests
- Slow down browser animations: F12 → Performance → CPU throttling
- Talk slowly and pause at key moments
- Zoom browser to 150% so text is visible on mobile

---

## **Shortcuts for Speed**

If running short on time:
1. **Skip registration**: Pre-create a user beforehand
2. **Skip account creation**: Create them beforehand
3. **Just do one transfer**: Show the full lifecycle for a single transfer
4. **Skip failover demo**: Tell them it works, show docs instead

---

## **Files to Share After Demo**

- This script: `web/DEMO_SCRIPT.md`
- Architecture docs: `docs/architecture.md`
- Event schemas: `docs/events.md`
- Failover verification: `docs/runbooks/failover-verification.md`
- CLAUDE.md: The full engineering spec

---

**Good luck! You've got this! 🚀**
