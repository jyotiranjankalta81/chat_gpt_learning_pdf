import type { NextFunction, Request, Response } from 'express';
import type { ZodSchema } from 'zod';
export function validateRequest(schema: ZodSchema) { return (req: Request, _res: Response, next: NextFunction) => { const parsed = schema.safeParse({ body: req.body, query: req.query, params: req.params }); if (!parsed.success) { next(parsed.error); return; } req.body = parsed.data.body ?? req.body; req.query = parsed.data.query ?? req.query; req.params = parsed.data.params ?? req.params; next(); }; }
