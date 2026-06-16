import { Router } from 'express';
import { SyncController } from '../../controllers/sync.controller.js';
import { requireAuth } from '../../middleware/auth.js';
import { validateRequest } from '../../middleware/validateRequest.js';
import { asyncHandler } from '../../utils/asyncHandler.js';
import { syncSchema } from '../../validators/job.validators.js';
const router = Router(); const controller = new SyncController();
router.post('/', requireAuth, validateRequest(syncSchema), asyncHandler(controller.enqueue));
export { router as syncRoutes };
