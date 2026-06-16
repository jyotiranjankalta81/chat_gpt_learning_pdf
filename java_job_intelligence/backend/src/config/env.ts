import dotenv from 'dotenv';
import { z } from 'zod';
dotenv.config();
const envSchema = z.object({ NODE_ENV: z.enum(['development', 'test', 'production']).default('development'), PORT: z.coerce.number().default(4000), MONGODB_URI: z.string().default('mongodb://localhost:27017/java_jobs'), REDIS_HOST: z.string().default('localhost'), REDIS_PORT: z.coerce.number().default(6379), REDIS_PASSWORD: z.string().optional(), JWT_SECRET: z.string().min(12).default('change-me-in-production'), CORS_ORIGIN: z.string().default('http://localhost:5173'), SYNC_CRON: z.string().default('0 6 * * *') });
export const env = envSchema.parse(process.env);
export const isProduction = env.NODE_ENV === 'production';
export const isTest = env.NODE_ENV === 'test';
