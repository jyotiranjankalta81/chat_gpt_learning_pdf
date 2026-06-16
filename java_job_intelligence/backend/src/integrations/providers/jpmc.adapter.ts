import { BaseCareerAdapter } from './baseCareerAdapter.js';
import { sampleJob } from './sampleJobs.js';
export class JPMCAdapter extends BaseCareerAdapter { constructor() { super({ companyName: 'JPMorgan Chase', source: 'JPMorgan Chase Careers', endpoint: process.env.JPMC_CAREERS_API, seedJobs: [sampleJob('JPMorgan Chase', 'java-backend-2-5', 'Mumbai, India'), sampleJob('JPMorgan Chase', 'senior-java-4-5', 'Remote, India')] }); } }
