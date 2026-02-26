const express = require('express');
const router = express.Router();
const { signinUser, getUsers } = require('../controller/userController'); 

// Login / Signin user
router.post('/users/login', signinUser);




module.exports = router;