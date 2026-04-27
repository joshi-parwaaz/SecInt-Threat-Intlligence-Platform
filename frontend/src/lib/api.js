/**
 * api.js - Centralised API base URL configuration
 *
 * In development:   reads from .env.local  →  REACT_APP_API_URL=http://localhost:8000
 * In production:    reads from Vercel env  →  REACT_APP_API_URL=https://secint-api.onrender.com
 *
 * All components import API_BASE from here instead of hardcoding localhost.
 */

export const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
