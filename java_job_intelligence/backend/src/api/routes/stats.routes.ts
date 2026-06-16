import { Router } from 'express';
import { JobController } from '../../controllers/job.controller.js';
import { asyncHandler } from '../../utils/asyncHandler.js';
const router = Router(); const controller = new JobController();
router.get('/', asyncHandler(controller.stats));
export { router as statsRoutes };
