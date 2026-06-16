import type { Request, Response } from 'express';
import { syncQueue } from '../queues/sync.queue.js';
export class SyncController { enqueue = async (_req: Request, res: Response): Promise<void> => { const job = await syncQueue.add('sync-java-jobs', {}, { removeOnComplete: 50, removeOnFail: 100 }); res.status(202).json({ message: 'Sync queued', queueJobId: job.id }); }; }
