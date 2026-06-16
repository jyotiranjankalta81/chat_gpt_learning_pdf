import type { ProviderJobInput } from '../../types.js';
export interface JobProvider { readonly companyName: string; fetchJobs(): Promise<ProviderJobInput[]>; }
