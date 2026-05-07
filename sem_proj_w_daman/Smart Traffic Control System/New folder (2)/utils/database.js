/**
 * Mock Database - In-memory user and account storage
 * In production, this would be replaced with MongoDB/MySQL
 */

// Users with hardcoded credentials for this exercise
const users = {
  'john_doe': {
    userId: 'user_001',
    username: 'john_doe',
    password: 'password123', // In production, use bcrypt
    email: 'john@example.com'
  },
  'jane_smith': {
    userId: 'user_002',
    username: 'jane_smith',
    password: 'securepass456', // In production, use bcrypt
    email: 'jane@example.com'
  }
};

// Bank accounts linked to users
const accounts = {
  'user_001': {
    accountId: 'acc_001',
    userId: 'user_001',
    accountNumber: '1234567890',
    accountHolder: 'John Doe',
    balance: 5000.00,
    currency: 'USD',
    createdAt: new Date('2024-01-15')
  },
  'user_002': {
    accountId: 'acc_002',
    userId: 'user_002',
    accountNumber: '9876543210',
    accountHolder: 'Jane Smith',
    balance: 10000.00,
    currency: 'USD',
    createdAt: new Date('2024-02-01')
  }
};

// Transaction history
const transactions = {
  'user_001': [],
  'user_002': []
};

/**
 * Find user by username
 */
const findUserByUsername = (username) => users[username];

/**
 * Get account for a user
 */
const getAccount = (userId) => accounts[userId];

/**
 * Get transaction history for a user
 */
const getTransactionHistory = (userId) => transactions[userId] || [];

/**
 * Update account balance
 */
const updateBalance = (userId, amount, type = 'deposit', description = '') => {
  const account = accounts[userId];
  if (!account) return null;

  const oldBalance = account.balance;
  account.balance += amount;

  // Record transaction
  if (!transactions[userId]) transactions[userId] = [];
  transactions[userId].push({
    transactionId: `txn_${Date.now()}`,
    type: type,
    amount: amount,
    oldBalance: oldBalance,
    newBalance: account.balance,
    description: description,
    timestamp: new Date()
  });

  return account;
};

/**
 * Check if user exists
 */
const userExists = (username) => !!users[username];

module.exports = {
  users,
  accounts,
  transactions,
  findUserByUsername,
  getAccount,
  getTransactionHistory,
  updateBalance,
  userExists
};
