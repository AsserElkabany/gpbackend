const express = require('express');
const router = express.Router();
const raspberryController = require('../controller/raspberryController');

// Add new scanner data (multiple networks)
router.post('/scanner', raspberryController.addScanners);
router.get('/scanner', raspberryController.getScanners);

router.post('/hashvalue',raspberryController.gethash)

// brute force WPA/WPA2/WPA3 endpoint - takes handshake id and brute forces it
router.post('/bruteforce/:id', raspberryController.bruteForceWPA);

module.exports = router;