import compression from 'compression';
import express from 'express';
import morgan from 'morgan';
import { apiRouter } from './api/routes/index.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';
import { apiRateLimiter, corsMiddleware, helmetMiddleware } from './middleware/security.js';
export function createApp(): express.Express { const app = express(); app.use(helmetMiddleware); app.use(corsMiddleware); app.use(apiRateLimiter); app.use(compression()); app.use(express.json({ limit: '1mb' })); app.use(morgan('combined')); app.use('/api', apiRouter); app.use(notFoundHandler); app.use(errorHandler); return app; }
