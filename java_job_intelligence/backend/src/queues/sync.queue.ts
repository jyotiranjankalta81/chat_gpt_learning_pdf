import { Queue } from 'bullmq';
import { redisConnectionOptions } from './connection.js';
export const syncQueue = new Queue('java-job-sync', { connection: redisConnectionOptions });
