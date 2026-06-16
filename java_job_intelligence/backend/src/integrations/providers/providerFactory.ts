import { AmazonAdapter } from './amazon.adapter.js';
import { GoogleAdapter } from './google.adapter.js';
import type { JobProvider } from './jobProvider.js';
import { JPMCAdapter } from './jpmc.adapter.js';
import { MicrosoftAdapter } from './microsoft.adapter.js';
import { OracleAdapter } from './oracle.adapter.js';
export class ProviderFactory { static createProviders(): JobProvider[] { return [new GoogleAdapter(), new MicrosoftAdapter(), new AmazonAdapter(), new OracleAdapter(), new JPMCAdapter()]; } }
