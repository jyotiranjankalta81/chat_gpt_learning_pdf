import type { Request, Response } from 'express';
import { CompanyService } from '../services/company.service.js';
export class CompanyController { constructor(private readonly companyService = new CompanyService()) {} list = async (_req: Request, res: Response): Promise<void> => { res.json(await this.companyService.listCompanies()); }; }
