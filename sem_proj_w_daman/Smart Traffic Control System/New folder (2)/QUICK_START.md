# JWT Banking API - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
npm install
```

### Step 2: Start the Server
```bash
npm start
```

**Output should show**: `Banking API server running on http://localhost:5000`

### Step 3: Test Login (Get JWT Token)
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"password123"}'
```

**Response will include**: `"token": "eyJhbGciOiJIUzI1NiIs..."`

### Step 4: Get Account Balance (Protected Route)
```bash
curl -X GET http://localhost:5000/api/banking/balance \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Replace `YOUR_TOKEN_HERE` with the token from Step 3.

### Step 5: Try Deposit
```bash
curl -X POST http://localhost:5000/api/banking/deposit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"amount":1000}'
```

## Test Credentials

| Username | Password | Initial Balance |
|----------|----------|-----------------|
| john_doe | password123 | $5,000 |
| jane_smith | securepass456 | $10,000 |

## Key Endpoints

| Method | Endpoint | Protected | Purpose |
|--------|----------|-----------|---------|
| POST | /api/auth/login | ❌ | Get JWT token |
| POST | /api/auth/register | ❌ | Register new user |
| POST | /api/auth/refresh | ❌ | Refresh JWT token |
| GET | /api/banking/balance | ✅ | Check account balance |
| POST | /api/banking/deposit | ✅ | Deposit money |
| POST | /api/banking/withdraw | ✅ | Withdraw money |
| GET | /api/banking/transactions | ✅ | View transaction history |

## Project Structure

```
.
├── server.js                      # Main Express app
├── package.json                   # Dependencies
├── .env                           # Environment config
├── middleware/
│   └── authMiddleware.js          # JWT verification
├── controllers/
│   ├── authController.js          # Auth logic
│   └── bankingController.js       # Banking logic
├── routes/
│   ├── authRoutes.js              # Auth endpoints
│   └── bankingRoutes.js           # Banking endpoints (protected)
├── utils/
│   └── database.js                # Mock database
└── documentation/
    ├── README.md                  # Full documentation
    ├── TESTING_GUIDE.md           # Comprehensive test guide
    └── POSTMAN_COLLECTION.json    # Postman collection
```

## Features Implemented

✅ **JWT Authentication**
- User login with hardcoded credentials
- Token generation and verification
- Token refresh mechanism
- Automatic token expiration

✅ **Banking Operations**
- View account balance
- Deposit funds
- Withdraw funds (with overdraft protection)
- Transaction history

✅ **Security**
- Protected routes require valid JWT
- Input validation
- Error handling
- User data isolation

✅ **Testing**
- Postman collection with all endpoints
- Comprehensive testing guide
- Test cases for all scenarios

## Troubleshooting

### Port Already in Use
```bash
# Change PORT in .env and restart
PORT=3000
npm start
```

### Module Not Found
```bash
# Reinstall dependencies
rm node_modules package-lock.json
npm install
```

### Token Errors
- Ensure token is from the same session (tokens reset on server restart)
- Check Authorization header format: `Bearer <token>`
- Use refresh endpoint if token expired

## Next Steps

1. **Import Postman Collection**:
   - Open Postman → Import → Select POSTMAN_COLLECTION.json
   - Use for interactive testing

2. **Read Full Documentation**:
   - See README.md for complete API documentation
   - See TESTING_GUIDE.md for detailed test procedures

3. **Enhanced Features** (for production):
   - Integrate with MongoDB/MySQL
   - Add bcrypt password hashing
   - Implement rate limiting
   - Add comprehensive logging
   - Write unit and integration tests

## Course Mapping

This experiment covers:

**CO3**: Implement RESTful APIs
- ✅ Created REST endpoints for banking operations
- ✅ Proper HTTP methods (GET, POST)
- ✅ JSON request/response handling
- ✅ Appropriate status codes

**CO4**: Debug, Test, and Optimize
- ✅ Comprehensive error handling
- ✅ Detailed test cases
- ✅ Performance optimized (in-memory operations)
- ✅ Security-focused implementation (JWT verification)

## Experiment Objectives Checklist

- ✅ Create user registration and login endpoints
- ✅ Generate and verify JWTs
- ✅ Protect banking routes
- ✅ Implement token refresh mechanisms
- ✅ Add account-level security
- ✅ Handle common errors
- ✅ Test API with Postman

---

**Status**: ✅ All objectives completed and ready for testing!
