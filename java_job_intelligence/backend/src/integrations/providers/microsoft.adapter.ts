import { BaseCareerAdapter } from './baseCareerAdapter.js';
import { sampleJob } from './sampleJobs.js';
export class MicrosoftAdapter extends BaseCareerAdapter { constructor() { super({ companyName: 'Microsoft', source: 'Microsoft Careers', endpoint: process.env.MICROSOFT_CAREERS_API, seedJobs: [sampleJob('Microsoft', 'java-backend-2-5', 'Hyderabad, India'), sampleJob('Microsoft', 'senior-java-4-5', 'Remote, India')] }); } }
