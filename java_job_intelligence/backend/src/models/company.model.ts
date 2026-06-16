import mongoose, { Schema, type HydratedDocument } from 'mongoose';
import type { CompanyDTO } from '../types.js';
export type CompanyDocument = HydratedDocument<CompanyDTO>;
const companySchema = new Schema<CompanyDTO>({ name: { type: String, required: true, unique: true, trim: true, index: true }, website: { type: String, required: true }, careerUrl: { type: String, required: true }, industry: { type: String, required: true, index: true }, country: { type: String, required: true, index: true }, indiaPresence: { type: Boolean, default: true, index: true }, active: { type: Boolean, default: true, index: true } }, { timestamps: true });
export const CompanyModel = mongoose.model<CompanyDTO>('Company', companySchema);
