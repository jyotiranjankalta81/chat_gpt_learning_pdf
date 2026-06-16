import { BaseCareerAdapter } from './baseCareerAdapter.js';
import { sampleJob } from './sampleJobs.js';
export class GoogleAdapter extends BaseCareerAdapter { constructor() { super({ companyName: 'Google', source: 'Google Careers', endpoint: process.env.GOOGLE_CAREERS_API, seedJobs: [sampleJob('Google', 'java-backend-2-5', 'Bengaluru, India'), sampleJob('Google', 'senior-java-4-5', 'Remote, India')] }); } }
