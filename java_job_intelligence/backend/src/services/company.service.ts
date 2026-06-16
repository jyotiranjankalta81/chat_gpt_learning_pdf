import { companyRegistry } from '../constants/companyRegistry.js';
import { CompanyRepository } from '../repositories/company.repository.js';
import type { CompanyDTO } from '../types.js';
export class CompanyService { constructor(private readonly companyRepository = new CompanyRepository()) {} async seedRegistry(): Promise<void> { await this.companyRepository.upsertMany(companyRegistry); } async listCompanies(): Promise<CompanyDTO[]> { await this.seedRegistry(); return this.companyRepository.findAll(); } async activeCompanies(): Promise<CompanyDTO[]> { await this.seedRegistry(); return this.companyRepository.findActive(); } }
