const express = require('express');
const router = express.Router();
const raspberryController = require('../controller/raspberryController');


router.post('/scanner', raspberryController.addScanners);
router.get('/scanner', raspberryController.getScanners);

//router.post('/hashvalue',raspberryController.gethash)


//router.post('/bruteforce/:id', raspberryController.bruteForceWPA);
router.post('/savepassword', raspberryController.savePassword);

module.exports = router;