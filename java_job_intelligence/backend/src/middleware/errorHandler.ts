import type { NextFunction, Request, Response } from 'express';
import { ZodError } from 'zod';
import { AppError } from '../utils/appError.js';
import { logger } from '../utils/logger.js';
export function notFoundHandler(req: Request, _res: Response, next: NextFunction): void { next(new AppError(`Route not found: ${req.method} ${req.originalUrl}`, 404)); }
export function errorHandler(error: unknown, _req: Request, res: Response, _next: NextFunction): void { if (error instanceof ZodError) { res.status(400).json({ message: 'Validation failed', issues: error.flatten() }); return; } if (error instanceof AppError) { res.status(error.statusCode).json({ message: error.message, details: error.details }); return; } logger.error('Unhandled API error', { error }); res.status(500).json({ message: 'Internal server error' }); }
