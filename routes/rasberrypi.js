const express = require('express');
const router = express.Router();
const raspberryController = require('../controller/raspberryController');


router.post('/scanner', raspberryController.addScanners);
router.get('/scanner', raspberryController.getScanners);

router.post('/savepassword', raspberryController.savePassword);

module.exports = router;