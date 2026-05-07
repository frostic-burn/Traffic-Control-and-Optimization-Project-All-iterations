const db = require('../utils/database');

/**
 * Get account balance
 * GET /api/banking/balance
 * Protected route - requires valid JWT
 */
const getBalance = (req, res) => {
  try {
    const userId = req.user.userId;

    // Get account from database
    const account = db.getAccount(userId);
    if (!account) {
      return res.status(404).json({ 
        error: 'Account not found',
        message: 'No account associated with this user'
      });
    }

    res.status(200).json({
      status: 'success',
      message: 'Balance retrieved successfully',
      data: {
        accountId: account.accountId,
        accountHolder: account.accountHolder,
        accountNumber: account.accountNumber,
        balance: account.balance,
        currency: account.currency,
        lastUpdated: new Date()
      }
    });
  } catch (error) {
    console.error('Get balance error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
};

/**
 * Deposit money to account
 * POST /api/banking/deposit
 * Protected route - requires valid JWT
 * Body: { amount: number, description: string (optional) }
 */
const deposit = (req, res) => {
  try {
    const userId = req.user.userId;
    const { amount, description } = req.body;

    // Validate input
    if (!amount || amount <= 0) {
      return res.status(400).json({ 
        error: 'Validation error',
        message: 'Amount must be a positive number'
      });
    }

    if (amount > 1000000) {
      return res.status(400).json({ 
        error: 'Validation error',
        message: 'Deposit amount cannot exceed 1,000,000'
      });
    }

    // Get account
    const account = db.getAccount(userId);
    if (!account) {
      return res.status(404).json({ 
        error: 'Account not found',
        message: 'No account associated with this user'
      });
    }

    // Update balance
    const oldBalance = account.balance;
    const updatedAccount = db.updateBalance(
      userId, 
      amount, 
      'deposit', 
      description || 'Deposit'
    );

    res.status(200).json({
      status: 'success',
      message: 'Deposit successful',
      data: {
        transactionId: `txn_${Date.now()}`,
        accountId: updatedAccount.accountId,
        accountHolder: updatedAccount.accountHolder,
        transactionType: 'deposit',
        amount: amount,
        oldBalance: oldBalance,
        newBalance: updatedAccount.balance,
        currency: updatedAccount.currency,
        description: description || 'Deposit',
        timestamp: new Date()
      }
    });
  } catch (error) {
    console.error('Deposit error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
};

/**
 * Withdraw money from account
 * POST /api/banking/withdraw
 * Protected route - requires valid JWT
 * Body: { amount: number, description: string (optional) }
 */
const withdraw = (req, res) => {
  try {
    const userId = req.user.userId;
    const { amount, description } = req.body;

    // Validate input
    if (!amount || amount <= 0) {
      return res.status(400).json({ 
        error: 'Validation error',
        message: 'Amount must be a positive number'
      });
    }

    if (amount > 1000000) {
      return res.status(400).json({ 
        error: 'Validation error',
        message: 'Withdrawal amount cannot exceed 1,000,000'
      });
    }

    // Get account
    const account = db.getAccount(userId);
    if (!account) {
      return res.status(404).json({ 
        error: 'Account not found',
        message: 'No account associated with this user'
      });
    }

    // Check sufficient balance
    if (account.balance < amount) {
      return res.status(400).json({ 
        error: 'Insufficient balance',
        message: `Available balance: ${account.balance}, Requested: ${amount}`
      });
    }

    // Update balance
    const oldBalance = account.balance;
    const updatedAccount = db.updateBalance(
      userId, 
      -amount, 
      'withdrawal', 
      description || 'Withdrawal'
    );

    res.status(200).json({
      status: 'success',
      message: 'Withdrawal successful',
      data: {
        transactionId: `txn_${Date.now()}`,
        accountId: updatedAccount.accountId,
        accountHolder: updatedAccount.accountHolder,
        transactionType: 'withdrawal',
        amount: amount,
        oldBalance: oldBalance,
        newBalance: updatedAccount.balance,
        currency: updatedAccount.currency,
        description: description || 'Withdrawal',
        timestamp: new Date()
      }
    });
  } catch (error) {
    console.error('Withdraw error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
};

/**
 * Get transaction history
 * GET /api/banking/transactions
 * Protected route - requires valid JWT
 */
const getTransactionHistory = (req, res) => {
  try {
    const userId = req.user.userId;

    const transactions = db.getTransactionHistory(userId);
    const account = db.getAccount(userId);

    if (!account) {
      return res.status(404).json({ 
        error: 'Account not found',
        message: 'No account associated with this user'
      });
    }

    res.status(200).json({
      status: 'success',
      message: 'Transaction history retrieved successfully',
      data: {
        accountId: account.accountId,
        accountHolder: account.accountHolder,
        currentBalance: account.balance,
        transactionCount: transactions.length,
        transactions: transactions
      }
    });
  } catch (error) {
    console.error('Get transaction history error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
};

module.exports = {
  getBalance,
  deposit,
  withdraw,
  getTransactionHistory
};
