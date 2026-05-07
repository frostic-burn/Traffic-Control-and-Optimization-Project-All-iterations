const jwt = require('jsonwebtoken');
const db = require('../utils/database');

/**
 * Login endpoint - Authenticate user and issue JWT token
 * POST /api/auth/login
 */
const login = (req, res) => {
  try {
    const { username, password } = req.body;

    // Validate input
    if (!username || !password) {
      return res.status(400).json({ 
        error: 'Validation error',
        message: 'Username and password are required'
      });
    }

    // Find user
    const user = db.findUserByUsername(username);
    if (!user) {
      return res.status(401).json({ 
        error: 'Authentication failed',
        message: 'Invalid username or password'
      });
    }

    // Verify password
    if (user.password !== password) {
      return res.status(401).json({ 
        error: 'Authentication failed',
        message: 'Invalid username or password'
      });
    }

    // Generate JWT token
    const payload = {
      userId: user.userId,
      username: user.username,
      email: user.email
    };

    const token = jwt.sign(payload, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_EXPIRES_IN || '1h'
    });

    // Generate refresh token
    const refreshToken = jwt.sign(payload, process.env.REFRESH_TOKEN_SECRET, {
      expiresIn: process.env.REFRESH_TOKEN_EXPIRES_IN || '7d'
    });

    res.status(200).json({
      status: 'success',
      message: 'Login successful',
      data: {
        userId: user.userId,
        username: user.username,
        email: user.email,
        token: token,
        refreshToken: refreshToken,
        expiresIn: process.env.JWT_EXPIRES_IN || '1h'
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
};

/**
 * Register endpoint - Create new user account
 * POST /api/auth/register
 */
const register = (req, res) => {
  try {
    const { username, password, email } = req.body;

    // Validate input
    if (!username || !password || !email) {
      return res.status(400).json({ 
        error: 'Validation error',
        message: 'Username, password, and email are required'
      });
    }

    // Check if user exists
    if (db.userExists(username)) {
      return res.status(400).json({ 
        error: 'User already exists',
        message: 'Username is already taken'
      });
    }

    // For this exercise, we'll just return success
    // In production, save to MongoDB/MySQL and hash password with bcrypt
    res.status(201).json({
      status: 'success',
      message: 'User registration successful (mock)',
      data: {
        username: username,
        email: email,
        message: 'In a real application, this would save to the database'
      }
    });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ 
      error: 'Server error',
      message: error.message 
    });
  }
};

/**
 * Refresh token endpoint - Issue new JWT using refresh token
 * POST /api/auth/refresh
 */
const refreshToken = (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({ 
        error: 'Validation error',
        message: 'Refresh token is required'
      });
    }

    // Verify refresh token
    const decoded = jwt.verify(refreshToken, process.env.REFRESH_TOKEN_SECRET);

    // Generate new JWT token
    const payload = {
      userId: decoded.userId,
      username: decoded.username,
      email: decoded.email
    };

    const newToken = jwt.sign(payload, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_EXPIRES_IN || '1h'
    });

    res.status(200).json({
      status: 'success',
      message: 'Token refreshed successfully',
      data: {
        token: newToken,
        expiresIn: process.env.JWT_EXPIRES_IN || '1h'
      }
    });
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ 
        error: 'Refresh token expired',
        message: 'Please login again'
      });
    }
    res.status(401).json({ 
      error: 'Invalid refresh token',
      message: error.message
    });
  }
};

module.exports = {
  login,
  register,
  refreshToken
};
