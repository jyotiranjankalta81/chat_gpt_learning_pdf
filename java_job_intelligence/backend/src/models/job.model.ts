import mongoose, { Schema, type HydratedDocument } from 'mongoose';
import type { JobDTO } from '../types.js';
export type JobDocument = HydratedDocument<JobDTO>;
const jobSchema = new Schema<JobDTO>({ jobId: { type: String, required: true, trim: true }, companyId: { type: Schema.Types.ObjectId, ref: 'Company', required: true, index: true }, title: { type: String, required: true, trim: true, index: true }, location: { type: String, required: true, trim: true, index: true }, employmentType: { type: String, required: true, default: 'Full-time' }, experienceMin: { type: Number, required: true, min: 0, index: true }, experienceMax: { type: Number, required: true, min: 0, index: true }, skills: [{ type: String, index: true }], salary: { type: String }, postedDate: { type: Date, index: true }, applyUrl: { type: String, required: true, index: true }, jobDescription: { type: String, required: true }, source: { type: String, required: true, index: true }, lastSeenAt: { type: Date, required: true, index: true }, isActive: { type: Boolean, default: true, index: true } }, { timestamps: true });
jobSchema.index({ companyId: 1, jobId: 1 }, { unique: true });
jobSchema.index({ title: 'text', jobDescription: 'text', location: 'text', skills: 'text' });
jobSchema.index({ title: 1, location: 1, applyUrl: 1 });
export const JobModel = mongoose.model<JobDTO>('Job', jobSchema);
