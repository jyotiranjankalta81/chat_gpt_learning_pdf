import mongoose from 'mongoose';
import { env } from '../config/env.js';
import { logger } from '../utils/logger.js';
export async function connectDatabase(uri = env.MONGODB_URI): Promise<void> { mongoose.set('strictQuery', true); await mongoose.connect(uri); logger.info('MongoDB connected'); }
export async function disconnectDatabase(): Promise<void> { await mongoose.disconnect(); logger.info('MongoDB disconnected'); }
