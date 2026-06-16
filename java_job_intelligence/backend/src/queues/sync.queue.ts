import { Queue } from 'bullmq';
import { redisConnection } from './connection.js';
export const syncQueue = new Queue('java-job-sync', { connection: redisConnection });
