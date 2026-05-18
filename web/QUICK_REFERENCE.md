# 🚀 Quick Reference Card - NanoBank Demo

## Access
```
http://localhost:8080
```

## Default Test Credentials
```
Username: demo_user
Email:    demo@test.local
Password: DemoPass123!
```

## Typical Demo Flow

### 1️⃣ Register User
- Fields: Username, Email, Password
- Expected: ✅ Registration successful
- Duration: 1-2 seconds
- Services: Auth → PostgreSQL

### 2️⃣ Login  
- Fields: Username, Password
- Expected: ✅ Login successful + JWT token
- Duration: 1-2 seconds
- Services: Auth → Redis (session storage)

### 3️⃣ Create 3 Accounts
- Currencies: USD, EUR, UAH (one each)
- Initial Balance: 1000.00 (automatic)
- Expected: ✅ Account created (×3)
- Duration: 1-2 seconds each
- Services: Core Banking → PostgreSQL

### 4️⃣ Execute Transfer ⭐
- From: USD Account
- To: EUR Account
- Amount: 100.00
- Expected: ✅ Transfer successful
- Duration: 1-2 seconds
- Services: Core Banking → PostgreSQL → RabbitMQ

### 5️⃣ View History
- Click: **Refresh History**
- Expected: Transaction appears (may take 1-3 seconds)
- Duration: 1-2 seconds
- Services: History (RabbitMQ consumer) → MongoDB

---

## Service Health Indicators

| Indicator | Status | Meaning |
|-----------|--------|---------|
| 🟢 Green | Online | Service responding normally |
| ⚫ Gray | Offline | Service unreachable |
| 🟡 Yellow | Starting | Service initializing |

Updates every 5 seconds automatically.

---

## Key Metrics to Highlight

### Registration/Login Flow
- **Password Hashing**: argon2id
- **Session Storage**: Redis (survives replica failure)
- **Token Type**: JWT with expiration
- **Load Balancing**: 2 Auth replicas, least_conn policy

### Account Management  
- **Database**: PostgreSQL (separate per service)
- **Account Storage**: Persistent, indexed by UUID
- **Initial Balance**: 1000.00 units
- **Multi-Currency**: USD, EUR, UAH supported

### Money Transfer (The Core Demo)
- **Transaction Type**: ACID (Atomicity, Consistency, Isolation, Durability)
- **Locking**: Deterministic row-level locks (prevents deadlocks)
- **Currency Conversion**: Fixed rates, happens atomically
- **Event Publishing**: Transactional outbox pattern (no message loss)
- **Event Consumer**: History Service (RabbitMQ-based)
- **Storage**: MongoDB replica set (w=majority concern)

---

## API Inspector Guide

```
REQUEST
├─ Method: POST/GET/etc
├─ Endpoint: /auth/register, /accounts, /transfers, /history
├─ Body: Request payload
└─ Authorization: Bearer JWT token

RESPONSE  
├─ Status: HTTP code (200, 201, 400, 422, etc)
├─ Badge: ✓ OK (green) or ✗ ERROR (red)
└─ Response: JSON response from service
```

**Color Coding**:
- 🟢 2xx: Success (200, 201, etc)
- 🔴 4xx/5xx: Error (422, 500, etc)

---

## Common Responses

### Successful Registration (201)
```json
{
  "status": true,
  "response": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "demo_user"
  }
}
```

### Successful Login (200)
```json
{
  "status": true,
  "response": {
    "access_token": "eyJhbGc...",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "expires_in": 1800
  }
}
```

### Account Created (201)
```json
{
  "status": true,
  "response": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "currency": "USD",
    "balance": 1000.0
  }
}
```

### Transfer Successful (200)
```json
{
  "status": true,
  "response": {
    "transaction_id": "770e8400-e29b-41d4-a716-446655440000",
    "from_account_id": "660e8400...",
    "to_account_id": "660e8400...",
    "amount": 100.0,
    "currency": "USD"
  }
}
```

---

## Troubleshooting

### All services show gray dots
**Problem**: Services not running  
**Solution**: 
```bash
docker-compose ps
docker-compose up -d
```

### 422 Error on Register/Login
**Problem**: Invalid input  
**Solution**:
- Password must contain: letters, numbers, special chars (!@#$%^&*)
- Username must be alphanumeric (no spaces)
- Email must be valid format

### Transfer fails with 400
**Problem**: Same account or invalid amount  
**Solution**:
- Select different accounts for From/To
- Amount must be > 0
- Ensure sufficient balance in source

### History shows "No transactions"
**Problem**: Event not consumed yet  
**Solution**:
- Wait 2-3 seconds
- Click **Refresh History** again
- Events are eventually consistent (CQRS pattern)

### Offline/Error in API Inspector
**Problem**: Service unreachable  
**Solution**:
- Check `docker-compose logs SERVICE_NAME`
- Wait for service startup (first request might be slow)
- Restart service: `docker-compose restart SERVICE_NAME`

---

## Keyboard Shortcuts

- `F12`: Open DevTools (see network requests)
- `Ctrl+Shift+I`: Toggle DevTools
- `Ctrl+1-5`: Chrome tab switching

---

## Pro Tips for Demo

1. **Have test data ready**: Pre-create accounts beforehand to save time
2. **Show DevTools**: Open F12 to show actual HTTP requests/responses
3. **Explain the 3 layers**: Routes (HTTP) → Services (Business Logic) → Database (Persistence)
4. **Point to the outbox pattern**: "Event is only published after transaction commits"
5. **Mention idempotency**: "History Service keyed on event_id prevents duplicate processing"
6. **Emphasize independence**: "Each service is independently deployable and scalable"

---

## Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Gateway (8080)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Auth Service (8001/8002) ×2 replicas                   │ │
│  │ ├─ Routes: /auth/*, /.well-known/*                     │ │
│  │ ├─ Storage: PostgreSQL                                 │ │
│  │ └─ Sessions: Redis                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Core Banking Service (8003)                            │ │
│  │ ├─ Routes: /accounts, /transfers                       │ │
│  │ ├─ Storage: PostgreSQL                                 │ │
│  │ └─ Events: RabbitMQ (transactional outbox)            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ History Service (8004)                                 │ │
│  │ ├─ Routes: /history                                    │ │
│  │ ├─ Consumer: RabbitMQ                                  │ │
│  │ └─ Storage: MongoDB Replica Set (3 nodes)             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ BankMarket Service (8005)                              │ │
│  │ ├─ Routes: /market/*                                   │ │
│  │ └─ Storage: Neo4j (recommendations)                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Time Estimates

| Action | Duration | Notes |
|--------|----------|-------|
| Register | 1-2s | First request slightly slower |
| Login | 1-2s | JWT generation takes ~100ms |
| Create Account | 1-2s | Per account |
| Transfer | 1-2s | ACID transaction + event publish |
| View History | 1-2s | Event consume delay: 0.5-3s |

**Total demo**: 5-10 minutes depending on pacing

---

## Important Concepts to Mention

- **ACID**: Atomicity (all or nothing), Consistency (valid state), Isolation (no interference), Durability (persisted)
- **CQRS**: Command Query Responsibility Segregation (separate write and read models)
- **Eventual Consistency**: History updates after a slight delay (normal in distributed systems)
- **Transactional Outbox**: Pattern that ensures event publishing only happens if database commit succeeds
- **Idempotency**: Processing same event multiple times produces same result (prevents duplicates)
- **Replica Failover**: If one Auth service goes down, Nginx routes to the other without user noticing

---

**Last Updated**: 2026-05-19  
**Version**: 1.0
