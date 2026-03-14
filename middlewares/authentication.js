const jwt = require('jsonwebtoken');
const jwtkey = "f3b7d6c9a42e1b8d907c4f6a2e1d3b4f7a9c0e5b2d1f6a8c3e7b4d9a6c2f1e0d3b5a7f8c9d4e1b2a3f6c8e9d0b1a2c3f4";

const verify = (req, res, next) => {
    const token = req.cookies["token"];
    console.log(token)
    if (!token) {
        return res.status(401).json({ error: "Token is required" });
    }
    try {
        const decoded = jwt.verify(token, jwtkey);
        //console.log({ "decoded token": decoded });

        if (!decoded) {
            return res.status(401).json({ error: "Invalid token" });
        }
        //console.log("Decoded token:", decoded);
        
        
        
        req.user_id = decoded.userId;
 

        next();
    } catch (err) {
        return res.status(401).json({ error: "Invalid token2" });
    }
};

module.exports = verify;