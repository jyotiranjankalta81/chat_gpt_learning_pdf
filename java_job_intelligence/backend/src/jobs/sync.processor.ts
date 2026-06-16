import { Worker } from 'bullmq';
import { redisConnectionOptions } from '../queues/connection.js';
import { JobIngestionService } from '../services/jobIngestion.service.js';
import { logger } from '../utils/logger.js';
export function startSyncWorker(): Worker { const worker = new Worker('java-job-sync', async () => new JobIngestionService().syncAll(), { connection: redisConnectionOptions, concurrency: 1 }); worker.on('completed', (job, result) => logger.info('Sync queue job completed', { id: job.id, result })); worker.on('failed', (job, error) => logger.error('Sync queue job failed', { id: job?.id, error })); return worker; }
