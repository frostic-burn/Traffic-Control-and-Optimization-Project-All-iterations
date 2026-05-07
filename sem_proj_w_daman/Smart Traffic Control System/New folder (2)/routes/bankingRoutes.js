const express = require('express');
const bankingController = require('../controllers/bankingController');
const verifyJWT = require('../middleware/authMiddleware');

const router = express.Router();

// All banking routes are protected - require valid JWT

/**
 * GET /api/banking/balance
 * Get account balance
 * Headers: Authorization: Bearer <token>
 */
router.get('/balance', verifyJWT, bankingController.getBalance);

/**
 * POST /api/banking/deposit
 * Deposit money to account
 * Headers: Authorization: Bearer <token>
 * Body: { amount: number, description: string (optional) }
 */
router.post('/deposit', verifyJWT, bankingController.deposit);

/**
 * POST /api/banking/withdraw
 * Withdraw money from account
 * Headers: Authorization: Bearer <token>
 * Body: { amount: number, description: string (optional) }
 */
router.post('/withdraw', verifyJWT, bankingController.withdraw);

/**
 * GET /api/banking/transactions
 * Get transaction history
 * Headers: Authorization: Bearer <token>
 */
router.get('/transactions', verifyJWT, bankingController.getTransactionHistory);

module.exports = router;
