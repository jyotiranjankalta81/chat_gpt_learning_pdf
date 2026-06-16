import cors from 'cors';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import { env } from '../config/env.js';
export const helmetMiddleware = helmet();
export const corsMiddleware = cors({ origin: env.CORS_ORIGIN, credentials: true });
export const apiRateLimiter = rateLimit({ windowMs: 60_000, limit: 120, standardHeaders: 'draft-7', legacyHeaders: false });
