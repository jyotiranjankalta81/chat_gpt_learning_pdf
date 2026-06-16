import { createApp } from './app.js';
import { env, isTest } from './config/env.js';
import { connectDatabase } from './database/mongoose.js';
import { startSyncWorker } from './jobs/sync.processor.js';
import { startDailySyncScheduler } from './schedulers/dailySync.scheduler.js';
import { logger } from './utils/logger.js';
async function bootstrap(): Promise<void> { await connectDatabase(); const app = createApp(); if (!isTest) { startSyncWorker(); startDailySyncScheduler(); } app.listen(env.PORT, () => logger.info('API server listening', { port: env.PORT })); }
bootstrap().catch((error) => { logger.error('Failed to start server', { error }); process.exit(1); });
