import type { NextFunction, Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import { env, isProduction } from '../config/env.js';
import { AppError } from '../utils/appError.js';
export function requireAuth(req: Request, _res: Response, next: NextFunction): void { if (!isProduction) { next(); return; } const token = req.headers.authorization?.replace(/^Bearer\s+/i, ''); if (!token) throw new AppError('Missing bearer token', 401); try { jwt.verify(token, env.JWT_SECRET); next(); } catch { next(new AppError('Invalid bearer token', 401)); } }
