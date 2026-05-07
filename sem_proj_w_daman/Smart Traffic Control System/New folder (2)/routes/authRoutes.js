const express = require('express');
const authController = require('../controllers/authController');

const router = express.Router();

/**
 * POST /api/auth/login
 * Login user and get JWT token
 * Body: { username: string, password: string }
 */
router.post('/login', authController.login);

/**
 * POST /api/auth/register
 * Register a new user
 * Body: { username: string, password: string, email: string }
 */
router.post('/register', authController.register);

/**
 * POST /api/auth/refresh
 * Refresh JWT token using refresh token
 * Body: { refreshToken: string }
 */
router.post('/refresh', authController.refreshToken);

module.exports = router;
