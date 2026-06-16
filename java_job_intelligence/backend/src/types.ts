import type { Types } from 'mongoose';
export interface CompanyDTO { _id?: string | Types.ObjectId; name: string; website: string; careerUrl: string; industry: string; country: string; indiaPresence: boolean; active: boolean; }
export interface JobDTO { _id?: string | Types.ObjectId; jobId: string; companyId: string | Types.ObjectId; companyName?: string; title: string; location: string; employmentType: string; experienceMin: number; experienceMax: number; skills: string[]; salary?: string; postedDate?: Date; applyUrl: string; jobDescription: string; source: string; lastSeenAt: Date; isActive: boolean; }
export interface ProviderJobInput extends Omit<JobDTO, 'companyId' | 'lastSeenAt' | 'isActive'> { companyName: string; }
export interface PaginatedResult<T> { items: T[]; page: number; limit: number; total: number; totalPages: number; }
export interface JobFilters { page: number; limit: number; search?: string; companyId?: string; location?: string; skill?: string; experienceMin?: number; experienceMax?: number; postedFrom?: Date; postedTo?: Date; sortBy: string; sortOrder: 'asc' | 'desc'; }
