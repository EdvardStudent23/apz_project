# 🏦 NanoBank - Interactive Microservices Demo

A modern, interactive web UI to demonstrate the full microservices workflow of the NanoBank system. Perfect for project defence presentations!

## 🎯 Features

### Complete Workflow Demonstration
- **User Registration & Authentication**: Register new users and authenticate via the Auth Service
- **Account Management**: Create accounts in different currencies (USD, EUR, UAH)
- **Money Transfers**: Execute ACID transfers between accounts with automatic currency conversion
- **Transaction History**: View complete transaction history powered by MongoDB
- **Service Health Monitoring**: Real-time indicators showing service availability

### Developer Features
- **Request/Response Inspector**: See all HTTP requests and responses in real-time
- **Detailed API Logging**: Complete request/response debugging information
- **Workflow Progress Tracking**: Visual step-by-step indication of the demonstration flow
- **Error Handling**: User-friendly error messages with helpful guidance

## 🚀 Quick Start

### Access the Dashboard
```
http://localhost:8080
```

The UI will automatically check service health on load and every 5 seconds.

## 📋 Demonstration Workflow

### Step 1: Register a User
1. Go to the **User Management** panel (left side)
2. Enter a username, email, and password
3. Click **Register User**
4. Watch the API Inspector to see the request/response flow

**Services involved**: Auth Service → PostgreSQL

### Step 2: Login
1. Switch to the **Login** tab
2. Enter your username and password
3. Click **Login**
4. Upon success, you'll see your User ID and current user info

**Services involved**: Auth Service → Redis (session storage) → JWT token generation

### Step 3: Create Accounts
1. Go to the **Account Management** panel (right side)
2. Select a currency (USD, EUR, or UAH)
3. Click **Create Account** - you'll get 1000.00 units as initial balance
4. Repeat for multiple currencies to demonstrate cross-currency transfers

**Services involved**: Core Banking Service → PostgreSQL

### Step 4: Execute Transfers
1. Go to the **Money Transfer** panel (bottom left)
2. Select "From Account" and "To Account"
3. Enter an amount
4. Click **Send Transfer**
5. The system will:
   - Lock accounts in ACID transaction
   - Convert currencies if needed
   - Debit source, credit destination
   - Publish event to RabbitMQ

**Services involved**: 
- Core Banking Service (ACID transfers, event publishing)
- RabbitMQ (transactional outbox pattern)

### Step 5: View Transaction History
1. Go to the **Transaction History** panel (bottom right)
2. Click **Refresh History**
3. See all transactions recorded by the History Service

**Services involved**: 
- History Service (RabbitMQ consumer)
- MongoDB Replica Set (with quorum-aware failover)

## 🔍 Understanding the Architecture

### Service Communication Flow

**Registration/Login**:
```
UI → Nginx Gateway → Auth Service (2 replicas)
                   → PostgreSQL (user storage)
                   → Redis (session storage)
```

**Account Creation**:
```
UI → Nginx Gateway → Core Banking Service
                   → PostgreSQL (account storage)
```

**Money Transfer** (CQRS pattern):
```
UI → Nginx Gateway → Core Banking Service
                   ├→ PostgreSQL (ACID transaction)
                   └→ RabbitMQ (event publishing)
                       → History Service Consumer
                           → MongoDB Replica Set
                               → Persisted event log
```

## 📊 Real-Time Features

### Service Health Indicators
- **Green dot**: Service is healthy and responding
- **Gray dot**: Service is unreachable
- Updates every 5 seconds

### API Inspector
The inspector at the bottom shows:
- **Timestamp**: When the request was made
- **Endpoint**: Which API endpoint was called
- **Status Code**: HTTP response code with visual badge
- **Request Details**: Full request payload (with passwords masked)
- **Response Details**: Complete JSON response from the service

### Workflow Steps
Visual progression through the 5-step workflow:
1. ✅ Register
2. 🔵 Login
3. 💳 Create Accounts
4. 💸 Transfer Money
5. 📜 View History

## 🎓 Project Defence Tips

### Talking Points to Highlight

**1. Authentication & Session Management**
- Two auth service replicas behind Nginx load balancing
- JWT tokens with expiration
- Redis-backed session storage (survives replica failover)
- Password hashing with argon2id

**2. ACID Transfers**
- Distributed transactions with row-level locking
- Deterministic lock ordering (prevents deadlocks)
- Automatic currency conversion with fixed rates
- Transactional event publishing (no message loss)

**3. Event-Driven Architecture**
- RabbitMQ topic exchange pattern
- History Service as read-side consumer (CQRS)
- Idempotent processing with event_id deduplication
- Dead-letter queue for failed messages

**4. Data Consistency**
- MongoDB replica set with quorum-aware failover
- Majority write concern (w=majority)
- Secondary-preferred read preference
- Automatic demotion to read-only on quorum loss

**5. Microservices Communication**
- Service discovery via Docker DNS
- JWT propagation across service boundaries
- Request ID tracing (x-request-id header)
- Independent data stores (no shared database)

### Demo Scenario for 5-10 Minutes

1. **Show the UI** (30 seconds)
   - Point out the service health indicators
   - Explain the workflow steps
   - Show the API Inspector

2. **Register and Login** (60 seconds)
   - Create a new user
   - Point out the JWT token in the inspector
   - Explain session storage in Redis

3. **Create Multiple Accounts** (60 seconds)
   - Create 2-3 accounts in different currencies
   - Show account balances
   - Mention PostgreSQL storage

4. **Execute a Transfer** (90 seconds)
   - Transfer money between accounts
   - Point out the ACID transaction properties
   - Show the request/response flow
   - Mention RabbitMQ event publishing
   - Wait ~2 seconds for History Service to consume event

5. **View History** (60 seconds)
   - Refresh transaction history
   - Show MongoDB storing the events
   - Explain eventual consistency
   - Mention replica set configuration

6. **Discuss Architecture** (Remaining time)
   - Explain the 3-tier per service
   - Talk about deployment resilience
   - Mention the failover capabilities

## 🛠 Technical Details

### Technologies Used
- **Frontend**: Vanilla HTML/CSS/JavaScript (no dependencies)
- **Styling**: CSS3 with responsive grid layout
- **API Communication**: Fetch API (modern async/await)
- **Real-time Updates**: 5-second polling for service health

### Browser Compatibility
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### Deployment
- Served as static file by Nginx
- No Node.js or build process required
- Can be modified live (restart Nginx to apply)

## 🐛 Troubleshooting

### "Service unavailable" errors
1. Check `docker-compose ps` to verify services are running
2. Wait 10-15 seconds after startup for services to be fully ready
3. Click the service health indicator to refresh

### CORS errors
- If running from a different domain, the UI won't work due to browser CORS
- Ensure you're accessing via `http://localhost:8080` (the gateway)

### 422 Validation errors
- Check that you're filling in all required fields
- Passwords must contain letters, numbers, and special characters
- Usernames must be alphanumeric (no spaces)

## 📝 Source Code

The UI is a single HTML file with:
- **~400 lines of CSS**: Responsive design with modern gradients
- **~600 lines of JavaScript**: API interaction and state management
- **~200 lines of HTML**: Semantic structure and form elements

**File**: `/web/index.html`

## 🎨 Customization

To modify the UI:

1. **Change colors**: Edit the CSS gradient values at the top
2. **Add more fields**: Add form groups to any panel
3. **Change the default initial balance**: Modify the `initial_balance` in `createAccount()`
4. **Add currency options**: Update the currency select with more options

After any changes:
```bash
docker-compose restart nginx
```

## 📚 Learning Resources

For understanding the architecture deeper:
- See `docs/architecture.md` for system design
- See `docs/events.md` for event schemas
- See individual service READMEs in `services/*/README.md`
- See `CLAUDE.md` for development guidelines

---

**Created for**: NanoBank Microservices Course Project  
**Version**: 1.0  
**Last Updated**: 2026-05-19
