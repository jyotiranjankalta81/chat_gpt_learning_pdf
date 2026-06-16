import { BaseCareerAdapter } from './baseCareerAdapter.js';
import { sampleJob } from './sampleJobs.js';
export class AmazonAdapter extends BaseCareerAdapter { constructor() { super({ companyName: 'Amazon', source: 'Amazon Careers', endpoint: process.env.AMAZON_CAREERS_API, seedJobs: [sampleJob('Amazon', 'java-backend-2-5', 'Bengaluru, India'), sampleJob('Amazon', 'senior-java-4-5', 'Remote, India')] }); } }
