const express = require('express');
const router = express.Router();
const raspberryController = require('../controller/raspberryController');
const authentication=require('../middlewares/authentication');

router.post('/scanner', authentication,raspberryController.addScanners);
router.get('/scanner', authentication,raspberryController.getScanners);

router.post('/savepassword',authentication, raspberryController.savePassword);

module.exports = router;