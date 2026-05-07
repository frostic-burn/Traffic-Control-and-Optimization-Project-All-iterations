const jwt = require('jsonwebtoken');

/**
 * Middleware to verify JWT token from Authorization header
 * Expected format: Authorization: Bearer <token>
 */
const verifyJWT = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    // Check if Authorization header exists
    if (!authHeader) {
      return res.status(401).json({ 
        error: 'Authorization header missing',
        message: 'Please provide Authorization header with Bearer token'
      });
    }

    // Extract token from "Bearer <token>"
    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
      return res.status(401).json({ 
        error: 'Invalid token format',
        message: 'Use format: Authorization: Bearer <token>'
      });
    }

    const token = parts[1];

    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ 
        error: 'Token expired',
        message: 'Please login again to get a new token'
      });
    }
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({ 
        error: 'Invalid token',
        message: 'Token verification failed'
      });
    }
    res.status(401).json({ 
      error: 'Token verification failed',
      message: error.message
    });
  }
};

module.exports = verifyJWT;
