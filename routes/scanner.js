const express = require('express');
const router = express.Router();
const { addScanner, getScanners } = require('../controller/scannerController');

// Add new scanner data
router.post('/scanner', addScanner);

// Get all scanner data
router.get('/scanner', getScanners);

module.exports = router;