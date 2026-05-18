# 📚 NanoBank Demo Documentation Index

## Quick Links

### 🎬 For Project Defence
- **Main Demo Guide**: [`../DEMO_GUIDE.md`](../DEMO_GUIDE.md) - Complete presentation guide with talking points
- **Demo Script**: [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) - Step-by-step walkthrough with timing
- **Quick Reference**: [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) - One-page cheat sheet

### 🖥️ For Using the Dashboard
- **Dashboard Documentation**: [`README.md`](README.md) - Feature overview and instructions
- **Live Dashboard**: [`index.html`](index.html) - The interactive UI (served at http://localhost:8080)

---

## 📖 Document Overview

| Document | Purpose | Audience | Read Time |
|----------|---------|----------|-----------|
| `DEMO_GUIDE.md` | Complete demo guide with architecture explanation | Presenters, panel members | 5 min |
| `DEMO_SCRIPT.md` | Step-by-step demo script with exact talking points | Presenters | 5 min |
| `QUICK_REFERENCE.md` | Cheat sheet and troubleshooting | Presenters during demo | 2 min |
| `README.md` | How to use the dashboard | End users | 10 min |
| `INDEX.md` | This file | Navigation | 1 min |

---

## 🚀 Getting Started (Pick One)

### Option A: I'm Presenting Tomorrow
1. Read: [`DEMO_GUIDE.md`](../DEMO_GUIDE.md) (5 minutes)
2. Read: [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) (5 minutes)
3. Print: [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md)
4. Practice: Run through the demo once (10 minutes)

**Total prep time: 30 minutes**

### Option B: I Want to Understand the UI
1. Read: [`README.md`](README.md)
2. Open: http://localhost:8080 in browser
3. Try: Register → Login → Create Accounts → Transfer

**Total time: 15 minutes**

### Option C: I'm the Panel/Evaluator
1. Skim: [`DEMO_GUIDE.md`](../DEMO_GUIDE.md) 
2. Reference: [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) during demo
3. Ask: Questions from "Talking Points" section

**Total time: 5 minutes**

---

## 🎯 Key Files

### Dashboard (`index.html`)
- **Size**: ~20KB (single HTML file, no build required)
- **Tech**: Vanilla JS, CSS3, Fetch API
- **Access**: `http://localhost:8080`
- **Features**: 
  - User registration & authentication
  - Account creation & management  
  - ACID money transfers
  - Transaction history viewer
  - Real-time API inspector
  - Service health monitoring

### Documentation Files
```
web/
├── index.html              ← The interactive dashboard
├── README.md               ← Dashboard user guide
├── DEMO_SCRIPT.md          ← Step-by-step demo script
├── QUICK_REFERENCE.md      ← Cheat sheet & troubleshooting
└── INDEX.md                ← This file
```

---

## 📊 What You Can Demonstrate

### ✅ User Management
- Register a new user with email and password
- Login with credentials
- See JWT token in API Inspector
- Understand session persistence via Redis

### ✅ Account Management
- Create accounts in multiple currencies (USD, EUR, UAH)
- See persistent storage in PostgreSQL
- View account balances
- Understand database per service pattern

### ✅ ACID Transfers (The Most Important Part)
- Transfer money between accounts
- Show atomic transaction in action
- Demonstrate currency conversion
- View the transactional outbox pattern

### ✅ Event-Driven Architecture
- See events published to RabbitMQ
- Watch History Service consume events
- View MongoDB replica set storage
- Explain eventual consistency (CQRS)

### ✅ Microservices Resilience
- Show 4 services communicating
- Watch real-time health indicators
- Explain replica failover capability
- Demonstrate independent deployability

---

## 🎬 Typical Demo Timeline (10 minutes)

| Time | Activity | Duration |
|------|----------|----------|
| 0:00 | Introduction & Architecture Overview | 1 min |
| 1:00 | Register User | 1 min |
| 2:00 | Login (show JWT) | 1 min |
| 3:00 | Create 3 Accounts | 1.5 min |
| 4:30 | Execute Transfer (⭐ Main Demo) | 2 min |
| 6:30 | View Transaction History | 1.5 min |
| 8:00 | Architecture Discussion | 2 min |

---

## 💡 Key Concepts to Explain

### Microservices
- 5 independent services with separate databases
- Each service owns its data (no shared schema)
- Services communicate via REST + RabbitMQ
- Independent deployability and scaling

### ACID Transactions
- **A**tomicity: Transfer happens all-or-nothing
- **C**onsistency: Account balance is always valid
- **I**solation: Concurrent transfers don't interfere
- **D**urability: Completed transfers persist

### Event-Driven Architecture
- Core Banking publishes events after transfer
- History Service consumes events asynchronously
- RabbitMQ provides message durability
- Enables eventual consistency for read models

### Distributed Systems Patterns
- **Saga Pattern**: Distributed transactions without 2PC
- **CQRS**: Command (write) and Query (read) separate
- **Transactional Outbox**: Ensures event publishing atomicity
- **Idempotency**: Processing events multiple times is safe

### Resilience Mechanisms
- **Replica Failover**: Auth has 2 replicas, load-balanced
- **Health Checks**: Nginx detects dead services
- **Circuit Breaking**: Automatic routing away from dead services
- **Quorum Awareness**: MongoDB goes read-only if majority lost

---

## 🔗 Related Documentation

### In the Repository
- **Architecture**: `../docs/architecture.md`
- **Vision & Use Cases**: `../docs/vision.md`, `../docs/use-cases.md`
- **Event Schemas**: `../docs/events.md`
- **Engineering Spec**: `../CLAUDE.md`
- **Failover Verification**: `../docs/runbooks/failover-verification.md`

### Service-Specific
- Auth Service: `../services/auth/README.md`
- Core Banking: `../services/core_banking/README.md`
- History Service: `../services/history/README.md`
- BankMarket: `../services/bankmarket/README.md`

---

## ❓ FAQ

### How long does a full demo take?
- **Quick version** (5 min): Register → Login → Transfer → History
- **Standard version** (10 min): Add account creation and architecture discussion
- **Extended version** (15 min): Add Q&A and failover demonstration

### Can I run this without Docker?
No, the demo requires the full Docker stack running. Microservices architecture requires multiple services running simultaneously.

### What if a service is offline?
The UI will show a gray health indicator. Restart services with `docker-compose restart SERVICE_NAME`.

### Can I modify the UI?
Yes! The HTML is in `index.html`. Make changes, restart Nginx with `docker-compose restart nginx`.

### Will this work for a recorded demo?
Yes! The UI is fully functional for recording. Just slow down your pacing and add voiceover explaining what's happening.

---

## ✅ Presentation Readiness Checklist

Before going live:
- [ ] Read DEMO_GUIDE.md completely
- [ ] Practice the demo script once (end-to-end)
- [ ] Verify all services are "Up" in `docker-compose ps`
- [ ] Test the UI loads at `http://localhost:8080`
- [ ] Have QUICK_REFERENCE.md printed
- [ ] Test your screen recording/presentation setup
- [ ] Have a backup plan (screenshots) if tech fails

---

## 🎓 Learning Outcomes

After the demo, the panel should understand:

1. **Architecture**: 5 services, independent databases, async messaging
2. **Financial Correctness**: ACID guarantees for money transfers
3. **Distributed Systems**: Event-driven, eventual consistency, saga pattern
4. **Resilience**: Replica failover, health checks, quorum awareness
5. **Practical Implementation**: Real code, real patterns, production-ready

---

## 📞 Need Help?

| Problem | Solution |
|---------|----------|
| Service won't start | Check `docker-compose logs SERVICE_NAME` |
| UI won't load | Restart Nginx: `docker-compose restart nginx` |
| Demo script questions | Check DEMO_SCRIPT.md for detailed explanations |
| Architecture questions | Check DEMO_GUIDE.md for architecture overview |
| Forgotten a detail? | Check QUICK_REFERENCE.md for quick lookup |

---

**Last Updated**: 2026-05-19  
**Version**: 1.0  
**For**: NanoBank Microservices Project Defence
