import { Router } from 'express';
import { CompanyController } from '../../controllers/company.controller.js';
import { asyncHandler } from '../../utils/asyncHandler.js';
const router = Router(); const controller = new CompanyController();
router.get('/', asyncHandler(controller.list));
export { router as companyRoutes };
