import cron from 'node-cron';
import { env } from '../config/env.js';
import { syncQueue } from '../queues/sync.queue.js';
import { logger } from '../utils/logger.js';
export function startDailySyncScheduler(): void { cron.schedule(env.SYNC_CRON, async () => { logger.info('Daily Java job sync triggered'); await syncQueue.add('daily-java-job-sync', {}, { removeOnComplete: 50, removeOnFail: 100 }); }, { timezone: 'Asia/Kolkata' }); logger.info('Daily sync scheduler registered', { cron: env.SYNC_CRON, timezone: 'Asia/Kolkata' }); }
