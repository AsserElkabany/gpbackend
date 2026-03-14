const express = require('express');
const router = express.Router();
const nmapController = require('../controller/nmapController');
const authentication=require('../middlewares/authentication');
router.post('/nmap',authentication, nmapController.saveNmapOutput);
router.get('/nmap',authentication, nmapController.getNmapScans);

module.exports = router;