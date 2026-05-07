# Testing Guide - JWT Banking API

## Overview
This document provides step-by-step testing procedures for the JWT Banking API experiment (2.3.2).

## Prerequisites
- Node.js server is running on `http://localhost:5000`
- Postman installed (or use curl/your preferred HTTP client)

## Test Users
```
User 1: john_doe / password123
User 2: jane_smith / securepass456
```

## Testing Workflow

### Phase 1: Verify Server is Running

**Test**: Health Check
- **Method**: GET
- **URL**: `http://localhost:5000/health`
- **Expected Status**: 200 OK
- **Response** should contain: `"message": "Banking API is running"`

---

### Phase 2: Authentication Testing

#### Test 2.1: Successful Login
**Objective**: Verify JWT token generation on successful login

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/auth/login`
   - Body:
     ```json
     {
       "username": "john_doe",
       "password": "password123"
     }
     ```

2. **Expected Response** (200 OK):
   - Contains `status: "success"`
   - Contains `token` (JWT access token)
   - Contains `refreshToken` (for token refresh)
   - Contains `expiresIn: "1h"`

3. **Save the token** for the next tests
   - Copy the `token` value
   - You'll use it as: `Authorization: Bearer <token>`

---

#### Test 2.2: Invalid Credentials
**Objective**: Verify authentication failure with wrong password

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/auth/login`
   - Body:
     ```json
     {
       "username": "john_doe",
       "password": "wrongpassword"
     }
     ```

2. **Expected Response** (401 Unauthorized):
   - Contains `"error": "Authentication failed"`
   - Contains `"message": "Invalid username or password"`

---

#### Test 2.3: Non-existent User
**Objective**: Verify error handling for non-existent username

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/auth/login`
   - Body:
     ```json
     {
       "username": "nonexistent_user",
       "password": "anypassword"
     }
     ```

2. **Expected Response** (401 Unauthorized):
   - Same error as Test 2.2

---

#### Test 2.4: Missing Credentials
**Objective**: Verify validation for empty fields

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/auth/login`
   - Body:
     ```json
     {
       "username": "john_doe"
     }
     ```

2. **Expected Response** (400 Bad Request):
   - Contains `"error": "Validation error"`
   - Contains `"message": "Username and password are required"`

---

### Phase 3: Protected Route Testing (JWT Verification)

#### Test 3.1: Access Protected Route WITH Valid Token
**Objective**: Verify successful access with valid JWT

1. **Prerequisites**:
   - Complete Test 2.1 and save the JWT token

2. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/balance`
   - Header: `Authorization: Bearer <your_token_from_test_2.1>`

3. **Expected Response** (200 OK):
   - Contains `status: "success"`
   - Contains balance information
   - Shows `accountHolder: "John Doe"`
   - Shows `balance: 5000`

---

#### Test 3.2: Access Protected Route WITHOUT Token
**Objective**: Verify denial of access with missing token

1. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/balance`
   - **NO Authorization header**

2. **Expected Response** (401 Unauthorized):
   - Contains `"error": "Authorization header missing"`
   - Contains `"message": "Please provide Authorization header with Bearer token"`

---

#### Test 3.3: Access Protected Route WITH Invalid Token
**Objective**: Verify error handling for malformed/invalid tokens

1. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/balance`
   - Header: `Authorization: Bearer invalid_jwt_token_xyz`

2. **Expected Response** (401 Unauthorized):
   - Contains `"error": "Invalid token"`
   - Contains `"message": "Token verification failed"`

---

#### Test 3.4: Invalid Bearer Format
**Objective**: Verify error handling for improper authorization format

1. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/balance`
   - Header: `Authorization: <your_token>` (missing "Bearer" prefix)

2. **Expected Response** (401 Unauthorized):
   - Contains `"error": "Invalid token format"`
   - Contains `"message": "Use format: Authorization: Bearer <token>"`

---

### Phase 4: Banking Operations Testing

#### Test 4.1: Get Account Balance
**Objective**: Verify balance retrieval

1. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/balance`
   - Header: `Authorization: Bearer <valid_token>`

2. **Expected Response** (200 OK):
   - John Doe: balance = 5000
   - Jane Smith: balance = 10000
   - Includes account metadata (accountId, accountNumber, currency)

---

#### Test 4.2: Deposit Money - Valid Transaction
**Objective**: Verify successful deposit

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/banking/deposit`
   - Header: `Authorization: Bearer <john_doe_token>`
   - Body:
     ```json
     {
       "amount": 1000.00,
       "description": "Salary"
     }
     ```

2. **Expected Response** (200 OK):
   - Contains `"message": "Deposit successful"`
   - Shows `oldBalance: 5000`
   - Shows `newBalance: 6000`
   - Includes `transactionId` and timestamp

3. **Verification**: Run Test 4.1 again to confirm new balance = 6000

---

#### Test 4.3: Deposit Money - Invalid Amount (Negative)
**Objective**: Verify validation for negative amounts

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/banking/deposit`
   - Header: `Authorization: Bearer <valid_token>`
   - Body:
     ```json
     {
       "amount": -500.00
     }
     ```

2. **Expected Response** (400 Bad Request):
   - Contains `"error": "Validation error"`
   - Contains `"message": "Amount must be a positive number"`

---

#### Test 4.4: Deposit Money - Zero Amount
**Objective**: Verify validation for zero amount

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/banking/deposit`
   - Header: `Authorization: Bearer <valid_token>`
   - Body:
     ```json
     {
       "amount": 0
     }
     ```

2. **Expected Response** (400 Bad Request):
   - Same validation error as Test 4.3

---

#### Test 4.5: Deposit Money - Excessive Amount
**Objective**: Verify validation for amounts exceeding limit

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/banking/deposit`
   - Header: `Authorization: Bearer <valid_token>`
   - Body:
     ```json
     {
       "amount": 2000000.00
     }
     ```

2. **Expected Response** (400 Bad Request):
   - Contains `"error": "Validation error"`
   - Contains `"message": "Deposit amount cannot exceed 1,000,000"`

---

#### Test 4.6: Withdraw Money - Valid Transaction (Sufficient Balance)
**Objective**: Verify successful withdrawal

1. **Prerequisites**:
   - John Doe's balance should be 6000 (after Test 4.2)

2. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/banking/withdraw`
   - Header: `Authorization: Bearer <john_doe_token>`
   - Body:
     ```json
     {
       "amount": 500.00,
       "description": "ATM withdrawal"
     }
     ```

3. **Expected Response** (200 OK):
   - Contains `"message": "Withdrawal successful"`
   - Shows `oldBalance: 6000`
   - Shows `newBalance: 5500`
   - Includes transaction details

4. **Verification**: Run Test 4.1 to confirm new balance = 5500

---

#### Test 4.7: Withdraw Money - Insufficient Balance
**Objective**: Verify overdraft protection

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/banking/withdraw`
   - Header: `Authorization: Bearer <john_doe_token>`
   - Body:
     ```json
     {
       "amount": 99999.00
     }
     ```

2. **Expected Response** (400 Bad Request):
   - Contains `"error": "Insufficient balance"`
   - Contains message showing available balance vs. requested amount
   - Example: `"Available balance: 5500, Requested: 99999"`

3. **Important**: Balance should NOT change after this failed transaction

---

#### Test 4.8: Withdraw Money - Negative Amount
**Objective**: Verify validation for negative withdrawal amounts

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/banking/withdraw`
   - Header: `Authorization: Bearer <valid_token>`
   - Body:
     ```json
     {
       "amount": -100.00
     }
     ```

2. **Expected Response** (400 Bad Request):
   - Contains validation error for negative amount

---

#### Test 4.9: Transaction History
**Objective**: Verify transaction history tracking

1. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/transactions`
   - Header: `Authorization: Bearer <john_doe_token>`

2. **Expected Response** (200 OK):
   - Contains all previous transactions
   - Examples from this test suite:
     - +1000 (Deposit - Test 4.2)
     - -500 (Withdrawal - Test 4.6)
   - Each transaction includes: type, amount, oldBalance, newBalance, timestamp

3. **Verification**:
   - Current balance should match the last transaction's newBalance
   - Transaction count should equal number of successful operations

---

### Phase 5: Token Refresh Testing

#### Test 5.1: Refresh Token - Valid Refresh Token
**Objective**: Verify token refresh functionality

1. **Prerequisites**:
   - Save the `refreshToken` from Test 2.1

2. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/auth/refresh`
   - Body:
     ```json
     {
       "refreshToken": "<your_refresh_token_from_test_2.1>"
     }
     ```

3. **Expected Response** (200 OK):
   - Contains new `token` (JWT access token)
   - Contains `expiresIn: "1h"`

4. **Verification**: 
   - Use the new token to access a protected route
   - Token should work like the original

---

#### Test 5.2: Refresh Token - Invalid Refresh Token
**Objective**: Verify error handling for invalid refresh tokens

1. **Request**:
   - Method: POST
   - URL: `http://localhost:5000/api/auth/refresh`
   - Body:
     ```json
     {
       "refreshToken": "invalid_refresh_token"
     }
     ```

2. **Expected Response** (401 Unauthorized):
   - Contains `"error": "Invalid refresh token"`

---

### Phase 6: Cross-User Security Testing

#### Test 6.1: User Isolation - John Cannot Access Jane's Account
**Objective**: Verify users can only access their own accounts

1. **Prerequisites**:
   - Get JWT token for john_doe (Test 2.1)
   - Get JWT token for jane_smith separately

2. **Data About Jane's Account**:
   - Jane Smith's balance = 10,000
   - Jane's account ID = acc_002

3. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/balance`
   - Header: `Authorization: Bearer <john_doe_token>`

4. **Expected Response** (200 OK):
   - Shows ONLY John Doe's account
   - Balance = John's balance (not Jane's 10,000)
   - This confirms user isolation

---

#### Test 6.2: Verify Jane Can Access Her Own Account
**Objective**: Confirm legitimate user access

1. **Request**:
   - Method: GET
   - URL: `http://localhost:5000/api/banking/balance`
   - Header: `Authorization: Bearer <jane_smith_token>`

2. **Expected Response** (200 OK):
   - Shows ONLY Jane Smith's account
   - Shows Jane's balance = 10,000

---

## Error Scenarios Summary

| Scenario | Status | Error Message |
|----------|--------|---------------|
| Missing Authorization header | 401 | Authorization header missing |
| Invalid token format | 401 | Invalid token format |
| Invalid/expired token | 401 | Invalid token / Token expired |
| Negative amount | 400 | Amount must be a positive number |
| Insufficient balance | 400 | Insufficient balance |
| Amount exceeds limit | 400 | Amount cannot exceed 1,000,000 |
| Account not found | 404 | Account not found |
| Invalid credentials | 401 | Invalid username or password |

## Postman Import Instructions

1. Open Postman
2. Click **Import** (top-left)
3. Select **POSTMAN_COLLECTION.json** from the project folder
4. Collection will be imported with all test cases
5. Replace Bearer tokens in test requests with actual tokens from login response

## Curl Command Examples

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"password123"}'
```

### Get Balance (requires token)
```bash
curl -X GET http://localhost:5000/api/banking/balance \
  -H "Authorization: Bearer <your_token>"
```

### Deposit
```bash
curl -X POST http://localhost:5000/api/banking/deposit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"amount":1000,"description":"Salary"}'
```

### Withdraw
```bash
curl -X POST http://localhost:5000/api/banking/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"amount":500,"description":"Withdrawal"}'
```

## Expected Results Summary

✅ Successful login generates valid JWT token  
✅ Protected routes reject requests without valid token  
✅ Deposits increase account balance  
✅ Withdrawals decrease account balance  
✅ Overdraft protection prevents negative balance  
✅ Transaction history tracks all operations  
✅ Token refresh generates new access token  
✅ User data remains isolated between accounts  
✅ All validation errors return appropriate HTTP status codes  

## Troubleshooting Test Failures

### "Bearer Token Expired"
- Get a new token by logging in again (Test 2.1)
- Refresh tokens can be used to get new access tokens (Test 5.1)

### "Amount must be a positive number"
- Ensure you're sending a number, not a string
- Verify amount > 0

### "Account not found"
- Ensure user is logged in correctly
- Check userId in JWT matches account in database

### "Insufficient balance for withdrawal"
- Check current balance first (Test 4.1)
- Reduce withdrawal amount below balance

## Performance Notes

- All tests complete in < 100ms typically
- Token generation takes ~5-10ms
- Database operations are in-memory (instant)

## Security Validation Checklist

- [ ] Tokens expire after 1 hour
- [ ] Refresh tokens expire after 7 days
- [ ] Protected routes reject unauthenticated requests
- [ ] Invalid tokens are rejected
- [ ] Passwords are NOT returned in any response
- [ ] User data is isolated (no cross-user access)
- [ ] Database remains stable after multiple operations
- [ ] Error messages don't leak sensitive information
