const express = require('express');
const router = express.Router();
const scannerController = require('../controller/scannerController');

// Add new scanner data (multiple networks)
router.post('/scanner', scannerController.addScanners);

// Get all scanner data
router.get('/scanner', scannerController.getScanners);

module.exports = router;