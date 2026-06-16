import { Router } from 'express';
import { JobController } from '../../controllers/job.controller.js';
import { validateRequest } from '../../middleware/validateRequest.js';
import { asyncHandler } from '../../utils/asyncHandler.js';
import { idParamSchema, listJobsSchema } from '../../validators/job.validators.js';
const router = Router(); const controller = new JobController();
router.get('/', validateRequest(listJobsSchema), asyncHandler(controller.list));
router.get('/:id', validateRequest(idParamSchema), asyncHandler(controller.getById));
export { router as jobRoutes };
