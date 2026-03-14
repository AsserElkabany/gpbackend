const express = require('express');
const router = express.Router();
const { signinUser, getUsers } = require('../controller/userController'); 
const authentication=require('../middlewares/authentication');

router.post('/users/login',signinUser);




module.exports = router;