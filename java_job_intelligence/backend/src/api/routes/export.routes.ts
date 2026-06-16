import { Router } from 'express';
import { JobController } from '../../controllers/job.controller.js';
import { validateRequest } from '../../middleware/validateRequest.js';
import { asyncHandler } from '../../utils/asyncHandler.js';
import { listJobsSchema } from '../../validators/job.validators.js';
const router = Router(); const controller = new JobController();
router.get('/excel', validateRequest(listJobsSchema), asyncHandler(controller.exportExcel));
export { router as exportRoutes };
