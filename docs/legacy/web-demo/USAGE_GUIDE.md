# 📖 NanoBank UI - What to Fill In Guide

## Quick Example Values

Use these when testing the UI:

| Field | Example Value | Notes |
|-------|---------------|-------|
| Username | `john_doe` | Alphanumeric, no spaces |
| Email | `john@example.com` | Valid email format |
| Password | `SecurePass123!` | Letters + numbers + special chars |
| Currency | `USD` | Choose USD, EUR, or UAH |
| Amount | `100.00` | Numbers with decimals |

---

## Step-by-Step: Complete Demo Flow

### 🟦 Step 1: Register User

**Location**: Left panel → "User Management" → "Register" tab

**What to fill:**

```
Username:     demo_user_1
Email:        demo@test.local
Password:     Demo123Pass!
```

**Rules:**
- Username: must be alphanumeric (letters, numbers only)
- Email: must be valid format (something@domain.com)
- Password: must have at least:
  - 1 uppercase letter (A-Z)
  - 1 lowercase letter (a-z)
  - 1 number (0-9)
  - 1 special character (!@#$%^&*)

**What happens:**
- Click "Register User"
- Wait 1-2 seconds
- See ✅ "Registration successful!" message

---

### 🟦 Step 2: Login

**Location**: Left panel → "User Management" → "Login" tab

**What to fill:**

```
Username:     demo_user_1
Password:     Demo123Pass!
```

**Important:** Use the same username and password from Step 1

**What happens:**
- Click "Login"
- Wait 1-2 seconds
- See ✅ "Login successful!" message
- See user info appear below with:
  - Logged in as: demo_user_1
  - User ID: (a long UUID string)
  - Logout button

**What you get:**
- JWT token (shown in API Inspector)
- Redis session stored
- Access to account management

---

### 🟦 Step 3: Create Accounts

**Location**: Right panel → "Account Management"

**What to fill (do this 3 times):**

**First Account:**
```
Currency:     USD
(Initial Balance is automatic: 1000.00)
```
Click "Create Account"

**Second Account:**
```
Currency:     EUR
```
Click "Create Account"

**Third Account:**
```
Currency:     UAH
```
Click "Create Account"

**What happens:**
- Each click creates a new account
- You'll see accounts listed below:
  ```
  USD Account
  1000.00 USD
  ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  
  EUR Account
  1000.00 EUR
  ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  
  UAH Account
  1000.00 UAH
  ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  ```

---

### 🟦 Step 4: Transfer Money ⭐ (Main Demo)

**Location**: Bottom left panel → "Money Transfer"

**What to fill:**

```
From Account:    USD Account (select from dropdown)
To Account:      EUR Account (select from dropdown)
Amount:          100.00
```

**Step-by-step:**

1. Click "From Account" dropdown → Select "USD - 1000.00"
2. Click "To Account" dropdown → Select "EUR - 1000.00"
3. Type in "Amount" field: `100.00`
4. Click "Send Transfer"

**Wait for response:**
- 1-2 seconds for the transfer
- See ✅ "Transfer successful!" message

**What you'll see:**
- Balances update:
  - USD Account: 900.00 (decreased)
  - EUR Account: ~1100.00 (increased, with currency conversion)

**In API Inspector:**
- Shows POST request to `/transfers`
- Shows status 200
- Shows transaction details

---

### 🟦 Step 5: View Transaction History

**Location**: Bottom right panel → "Transaction History"

**What to fill:**
```
(Nothing to fill - just click the button)
```

**Step-by-step:**

1. Click "Refresh History"
2. Wait 1-3 seconds
3. See the transaction appear:
   ```
   Transfer
   100.00 USD
   May 19, 2026, 10:30:45 AM
   ```

**What you're seeing:**
- Transaction recorded by History Service
- Powered by MongoDB
- Eventually consistent (slight delay is normal)

---

## 🎯 Quick Reference - What Goes Where

### User Management Panel (Left)

```
┌─ REGISTER TAB
│  ├─ Username: alphanumeric only
│  ├─ Email: valid@email.com
│  └─ Password: Strong (upper+lower+number+special)
│
└─ LOGIN TAB
   ├─ Username: same as registered
   └─ Password: same as registered
```

### Account Management Panel (Right)

```
┌─ CREATE ACCOUNT
│  └─ Currency: USD / EUR / UAH
│     (Balance auto-filled: 1000.00)
│
└─ YOUR ACCOUNTS (auto-populated after creation)
   ├─ Currency
   ├─ Balance
   └─ Account ID
```

### Money Transfer Panel (Bottom Left)

```
┌─ TRANSFER
   ├─ From Account: (dropdown - select an account)
   ├─ To Account: (dropdown - select different account)
   └─ Amount: (number, e.g., 100.00)
```

### Transaction History Panel (Bottom Right)

```
┌─ REFRESH HISTORY
│  (Button only, no fields to fill)
│
└─ TRANSACTION LIST (auto-populated)
   ├─ Transaction Type
   ├─ Amount
   └─ Timestamp
```

---

## ⚠️ Common Mistakes & Fixes

### "Please fill all fields"
**Problem**: Left a field empty  
**Fix**: Make sure all form fields have values before clicking button

### "422 Error" on Register
**Problem**: Password too weak  
**Fix**: Use password with:
- Uppercase: A-Z
- Lowercase: a-z
- Number: 0-9
- Special: !@#$%^&*

Example: `Demo123Pass!` ✅

### "Cannot transfer to same account"
**Problem**: Selected same account for From and To  
**Fix**: Select different accounts
- From: USD Account
- To: EUR Account ✓

### "History shows No transactions"
**Problem**: Waited too long or didn't complete transfer  
**Fix**: Wait 2-3 seconds after transfer, then click "Refresh History"
(This is normal - eventual consistency)

### "Service shows gray dot"
**Problem**: Service is down  
**Fix**: Wait 10 seconds or restart:
```bash
docker-compose restart SERVICE_NAME
```

---

## 📝 Test Scenario Script

**Run this exact sequence (5 minutes):**

```
1. Register:
   Username: test_user_1
   Email:    test1@local
   Password: Test123Pass!
   
2. Login:
   Username: test_user_1
   Password: Test123Pass!
   
3. Create Accounts (×3):
   Account 1: USD → Create Account
   Account 2: EUR → Create Account
   Account 3: UAH → Create Account
   
4. Transfer:
   From: USD Account (1000.00)
   To:   EUR Account (1000.00)
   Amount: 100.00
   
5. History:
   Click "Refresh History"
   Wait 2 seconds
   See transaction appear
```

---

## 🎓 What Each Field Does

### Username
- **Used for**: Login authentication
- **Format**: Alphanumeric only (no special chars, no spaces)
- **Example**: `john_doe`, `user123`, `demo_user_1`
- **Where**: Auth Service (PostgreSQL)

### Email
- **Used for**: User identification and contact
- **Format**: Valid email format
- **Example**: `john@example.com`, `test@local`
- **Where**: Auth Service (PostgreSQL)

### Password
- **Used for**: Secure authentication
- **Format**: Min 8 chars, must have:
  - 1 uppercase (A-Z)
  - 1 lowercase (a-z)
  - 1 number (0-9)
  - 1 special (!@#$%^&*)
- **Example**: `Demo123Pass!`, `Secure99!`
- **Where**: Auth Service (hashed with argon2id)

### Currency (Account)
- **Used for**: Account denomination
- **Options**: USD, EUR, UAH
- **Example**: USD
- **Where**: Core Banking Service (PostgreSQL)

### From Account
- **Used for**: Source of transfer (money withdrawn from here)
- **Format**: Select from dropdown
- **Example**: USD Account - 1000.00
- **Where**: Core Banking Service (ACID transaction)

### To Account
- **Used for**: Destination of transfer (money deposited here)
- **Format**: Select from dropdown
- **Important**: Must be different from "From Account"
- **Example**: EUR Account - 1000.00
- **Where**: Core Banking Service (ACID transaction)

### Amount
- **Used for**: How much to transfer
- **Format**: Number with decimals
- **Example**: `100.00`, `50.50`, `999.99`
- **Rules**:
  - Must be > 0
  - Must not exceed source account balance
  - Can have decimals (cents)
- **Where**: Core Banking Service (currency conversion)

---

## 🔄 Data Flow

```
USER INPUT
    ↓
FORM VALIDATION
    ├─ Are all fields filled?
    ├─ Is format correct?
    └─ Is value valid?
    ↓
API REQUEST
    ├─ POST /auth/register
    ├─ POST /auth/login
    ├─ POST /accounts
    ├─ POST /transfers
    └─ GET /history
    ↓
MICROSERVICE PROCESSING
    ├─ Auth Service (register/login)
    ├─ Core Banking (accounts/transfers)
    └─ History Service (transaction records)
    ↓
DATABASE STORAGE
    ├─ PostgreSQL (users, accounts)
    ├─ Redis (sessions)
    ├─ MongoDB (history)
    └─ RabbitMQ (events)
    ↓
UI UPDATE
    ├─ Show success/error message
    ├─ Update account balances
    ├─ Show transaction history
    └─ Update workflow steps
```

---

**Ready to demo? Start with the Test Scenario Script above! 🚀**
