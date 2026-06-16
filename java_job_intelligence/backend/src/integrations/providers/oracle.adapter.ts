import { BaseCareerAdapter } from './baseCareerAdapter.js';
import { sampleJob } from './sampleJobs.js';
export class OracleAdapter extends BaseCareerAdapter { constructor() { super({ companyName: 'Oracle', source: 'Oracle Careers', endpoint: process.env.ORACLE_CAREERS_API, seedJobs: [sampleJob('Oracle', 'java-backend-2-5', 'Bengaluru, India'), sampleJob('Oracle', 'senior-java-4-5', 'Remote, India')] }); } }
