const User = require('../models/User');
const jwt = require('jsonwebtoken');

const jwtkey = "f3b7d6c9a42e1b8d907c4f6a2e1d3b4f7a9c0e5b2d1f6a8c3e7b4d9a6c2f1e0d3b5a7f8c9d4e1b2a3f6c8e9d0b1a2c3f4";

exports.signinUser = async (req, res) => {
    try {
        const { username, password } = req.body;

        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password required' });
        }

        console.log(username, password);

        const user = await User.findOne({ username });

        if (!user) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        console.log("user found");

        if (user.password !== password) {   // ← Note: in production use bcrypt.compare!
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        user.lastLogin = new Date();
        await user.save();

        const token = jwt.sign(
            {
                id: user._id,
                username: user.username,
                email: user.email
            },
            jwtkey,
            { expiresIn: "24h" }
        );

        // ── Set secure HttpOnly cookie ───────────────────────────────────────
    res.cookie("token", token, {
  httpOnly: false,        // allow JS access
  sameSite: "lax",        // easier for local development
  secure: false,          // must be false if using HTTP
  path: "/",
  maxAge: 24 * 60 * 60 * 1000
});


        // Send success response (no need to send token in body anymore)
        res.status(200).json({
            message: "Login successful",
            user: {
                id: user._id,
                username: user.username,
                email: user.email
            }
        });

    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Login failed' });
    }
};