import type { ConnectionOptions } from 'bullmq';
import { env } from '../config/env.js';
export const redisConnectionOptions: ConnectionOptions = {
  host: env.REDIS_HOST,
  port: env.REDIS_PORT,
  password: env.REDIS_PASSWORD || undefined
};
