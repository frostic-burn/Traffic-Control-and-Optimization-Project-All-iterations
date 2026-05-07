# JWT Banking API - Experiment 2.3.2

JWT-based authentication implementation for a banking API with Node.js and Express.js.

## Course Outcomes Mapped
- **CO3**: Implement RESTful APIs and integrate databases (MongoDB/MySQL) with a backend server using Node.js and Express.js
- **CO4**: Debug, test, and optimize full-stack applications by analyzing performance and security aspects

## Objectives
✅ Create user registration and login endpoints  
✅ Generate and verify JWTs  
✅ Protect banking routes with middleware  
✅ Implement token refresh mechanisms  
✅ Add account-level security  
✅ Handle errors (missing tokens, invalid tokens, insufficient balance)  

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Configuration
The `.env` file is already configured for development. For production:
- Change `NODE_ENV` to `production`
- Update `JWT_SECRET` to a strong, random secret
- Update `REFRESH_TOKEN_SECRET` to a strong, random secret

```bash
# View current environment variables
cat .env
```

### 3. Start the Server
```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

The API will be running at `http://localhost:5000`

## API Endpoints

### Authentication Endpoints (Public)

#### 1. Login
**POST** `/api/auth/login`
```json
{
  "username": "john_doe",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "userId": "user_001",
    "username": "john_doe",
    "email": "john@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": "1h"
  }
}
```

#### 2. Register
**POST** `/api/auth/register`
```json
{
  "username": "new_user",
  "password": "securepass123",
  "email": "user@example.com"
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "message": "User registration successful (mock)",
  "data": {
    "username": "new_user",
    "email": "user@example.com",
    "message": "In a real application, this would save to the database"
  }
}
```

#### 3. Refresh Token
**POST** `/api/auth/refresh`
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Token refreshed successfully",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": "1h"
  }
}
```

### Banking Endpoints (Protected - Require JWT)

**Authorization Header Required**:  
All banking endpoints require the JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

#### 1. Get Account Balance
**GET** `/api/banking/balance`

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Balance retrieved successfully",
  "data": {
    "accountId": "acc_001",
    "accountHolder": "John Doe",
    "accountNumber": "1234567890",
    "balance": 5000.00,
    "currency": "USD",
    "lastUpdated": "2024-04-06T10:30:00.000Z"
  }
}
```

#### 2. Deposit Money
**POST** `/api/banking/deposit`

**Body**:
```json
{
  "amount": 1500.00,
  "description": "Salary deposit"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Deposit successful",
  "data": {
    "transactionId": "txn_1712403000000",
    "accountId": "acc_001",
    "accountHolder": "John Doe",
    "transactionType": "deposit",
    "amount": 1500.00,
    "oldBalance": 5000.00,
    "newBalance": 6500.00,
    "currency": "USD",
    "description": "Salary deposit",
    "timestamp": "2024-04-06T10:30:00.000Z"
  }
}
```

#### 3. Withdraw Money
**POST** `/api/banking/withdraw`

**Body**:
```json
{
  "amount": 500.00,
  "description": "ATM withdrawal"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Withdrawal successful",
  "data": {
    "transactionId": "txn_1712403000001",
    "accountId": "acc_001",
    "accountHolder": "John Doe",
    "transactionType": "withdrawal",
    "amount": 500.00,
    "oldBalance": 6500.00,
    "newBalance": 6000.00,
    "currency": "USD",
    "description": "ATM withdrawal",
    "timestamp": "2024-04-06T10:30:00.000Z"
  }
}
```

#### 4. Get Transaction History
**GET** `/api/banking/transactions`

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Transaction history retrieved successfully",
  "data": {
    "accountId": "acc_001",
    "accountHolder": "John Doe",
    "currentBalance": 6000.00,
    "transactionCount": 2,
    "transactions": [
      {
        "transactionId": "txn_1712403000000",
        "type": "deposit",
        "amount": 1500.00,
        "oldBalance": 5000.00,
        "newBalance": 6500.00,
        "description": "Salary deposit",
        "timestamp": "2024-04-06T10:30:00.000Z"
      },
      {
        "transactionId": "txn_1712403000001",
        "type": "withdrawal",
        "amount": 500.00,
        "oldBalance": 6500.00,
        "newBalance": 6000.00,
        "description": "ATM withdrawal",
        "timestamp": "2024-04-06T10:30:00.000Z"
      }
    ]
  }
}
```

## Test Users (Hardcoded for this Exercise)

| Username | Password | Email | Account Balance |
|----------|----------|--------|-----------------|
| john_doe | password123 | john@example.com | $5,000.00 |
| jane_smith | securepass456 | jane@example.com | $10,000.00 |

## Testing with Postman

### Step 1: Login and Get Token
- **Method**: POST
- **URL**: `http://localhost:5000/api/auth/login`
- **Body** (JSON):
  ```json
  {
    "username": "john_doe",
    "password": "password123"
  }
  ```
- **Copy the token** from the response

### Step 2: Access Protected Routes
For any banking endpoint, add the Authorization header:
- **Header Key**: `Authorization`
- **Header Value**: `Bearer <paste_token_here>`

### Step 3: Test Secure Access
1. **Get Balance** (GET): `http://localhost:5000/api/banking/balance`
2. **Deposit** (POST): `http://localhost:5000/api/banking/deposit`
   - Body: `{"amount": 1000}`
3. **Withdraw** (POST): `http://localhost:5000/api/banking/withdraw`
   - Body: `{"amount": 500}`
4. **Check Balance Again** (GET): `http://localhost:5000/api/banking/balance`

### Step 4: Try Accessing Without Token
- **Method**: GET
- **URL**: `http://localhost:5000/api/banking/balance`
- **No Authorization header**
- **Expected Response**: 401 Unauthorized

## Error Handling

### Missing Authorization Header
**Status**: 401 Unauthorized
```json
{
  "error": "Authorization header missing",
  "message": "Please provide Authorization header with Bearer token"
}
```

### Invalid Token Format
**Status**: 401 Unauthorized
```json
{
  "error": "Invalid token format",
  "message": "Use format: Authorization: Bearer <token>"
}
```

### Expired Token
**Status**: 401 Unauthorized
```json
{
  "error": "Token expired",
  "message": "Please login again to get a new token"
}
```

### Insufficient Balance
**Status**: 400 Bad Request
```json
{
  "error": "Insufficient balance",
  "message": "Available balance: 5000, Requested: 6000"
}
```

### Invalid Amount
**Status**: 400 Bad Request
```json
{
  "error": "Validation error",
  "message": "Amount must be a positive number"
}
```

## Security Features Implemented

✅ **JWT Authentication**: Signed tokens with expiration  
✅ **Token Refresh**: Long-lived refresh tokens for obtaining new access tokens  
✅ **Protected Routes**: Middleware validates token before accessing banking endpoints  
✅ **Error Handling**: Comprehensive error messages for debugging  
✅ **Balance Validation**: Prevents overdrafts  
✅ **Transaction History**: Tracks all transactions with timestamps  
✅ **Environment Configuration**: Sensitive data in .env file  

## Project Structure

```
jwt-banking-api/
├── server.js                 # Main Express application
├── package.json              # Dependencies
├── .env                       # Environment variables (configured)
├── .env.example               # Environment template
├── README.md                  # This file
├── middleware/
│   └── authMiddleware.js      # JWT verification middleware
├── controllers/
│   ├── authController.js      # Authentication logic (login, register, refresh)
│   └── bankingController.js   # Banking endpoints (balance, deposit, withdraw)
├── routes/
│   ├── authRoutes.js          # Auth endpoint routes
│   └── bankingRoutes.js       # Protected banking routes
└── utils/
    └── database.js            # Mock database (users, accounts, transactions)
```

## Key Implementation Details

### 1. JWT Middleware (`middleware/authMiddleware.js`)
- Extracts token from "Bearer <token>" format
- Verifies token signature and expiration
- Passes decoded user data to route handlers
- Returns appropriate error for missing/invalid tokens

### 2. Authentication Controller (`controllers/authController.js`)
- **Login**: Validates credentials and issues JWT + refresh token
- **Register**: Template for user registration (mock implementation)
- **Refresh Token**: Validates refresh token and issues new JWT

### 3. Banking Controller (`controllers/bankingController.js`)
- **Get Balance**: Returns current account balance
- **Deposit**: Adds funds and records transaction
- **Withdraw**: Subtracts funds with overdraft protection
- **Transaction History**: Shows all past transactions

### 4. Mock Database (`utils/database.js`)
- In-memory storage for users, accounts, and transactions
- Ready for migration to MongoDB/MySQL
- Maintains transaction history

## Enhancement Opportunities

For production deployment, consider:

1. **Database Integration**:
   - Replace mock database with MongoDB or MySQL
   - Use Mongoose or Sequelize for ORM

2. **Password Security**:
   - Use bcrypt for password hashing instead of plaintext comparison
   ```javascript
   const bcrypt = require('bcrypt');
   const hashedPassword = await bcrypt.hash(password, 10);
   ```

3. **Input Validation**:
   - Use libraries like Joi or Yup for schema validation
   - Validate email format and strong passwords

4. **Rate Limiting**:
   - Prevent brute force attacks on login
   - Use express-rate-limit middleware

5. **HTTPS**:
   - Deploy with SSL/TLS certificates
   - Use secure cookie flags

6. **Logging**:
   - Implement comprehensive logging for audit trails
   - Use Winston or Morgan for structured logging

7. **Testing**:
   - Write unit tests for controllers
   - Integration tests for API endpoints
   - Use Jest or Mocha

## Troubleshooting

### "Cannot find module 'express'"
```bash
npm install
```

### "TypeError: Cannot read property 'userId' of undefined"
- Ensure Authorization header is included
- Verify token is not expired
- Use correct token format: `Bearer <token>`

### "Insufficient balance" error
- Check current balance with GET /api/banking/balance
- Ensure withdrawal amount is less than available balance

### Token not working after restart
- All tokens are invalidated when server restarts (in-file mode)
- Login again to get a new token
- In production, use persistent token storage (Redis)

## License
Educational Use Only

## Authors
Course CO3 & CO4 Technical Implementation
