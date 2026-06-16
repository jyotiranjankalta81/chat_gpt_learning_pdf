import mongoose, { Schema, type HydratedDocument } from 'mongoose';
export type JobChangeType = 'created' | 'updated' | 'deactivated' | 'seen';
export interface JobHistoryDTO { jobId: mongoose.Types.ObjectId | string; changeType: JobChangeType; timestamp: Date; metadata?: Record<string, unknown>; }
export type JobHistoryDocument = HydratedDocument<JobHistoryDTO>;
const jobHistorySchema = new Schema<JobHistoryDTO>({ jobId: { type: Schema.Types.ObjectId, ref: 'Job', required: true, index: true }, changeType: { type: String, required: true, enum: ['created', 'updated', 'deactivated', 'seen'], index: true }, timestamp: { type: Date, required: true, default: Date.now, index: true }, metadata: { type: Schema.Types.Mixed } }, { timestamps: false });
export const JobHistoryModel = mongoose.model<JobHistoryDTO>('JobHistory', jobHistorySchema);
