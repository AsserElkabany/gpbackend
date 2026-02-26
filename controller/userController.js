const User = require('../models/User');

// Sign in / login
exports.signinUser = async (req, res) => {
    try {
        const { username, password } = req.body;

        // Check required fields
        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password required' });
        }

        // Find user by username
        const user = await User.findOne({ username });
        if (!user) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Check password (plain text)
        if (user.password !== password) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Optional: update last login (if you want)
        user.lastLogin = new Date();
        await user.save();

        // Return user info (without token or role)
        res.json({
            message: "Login successful",
            user: {
                id: user._id,
                username: user.username,
                email: user.email,
                // password is omitted for security
            }
        });

    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Login failed' });
    }
};