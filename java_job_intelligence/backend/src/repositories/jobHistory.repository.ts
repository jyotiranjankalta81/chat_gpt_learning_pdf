import { JobHistoryModel, type JobChangeType } from '../models/jobHistory.model.js';
export class JobHistoryRepository { async record(jobId: string, changeType: JobChangeType, metadata?: Record<string, unknown>): Promise<void> { await JobHistoryModel.create({ jobId, changeType, timestamp: new Date(), metadata }); } }
