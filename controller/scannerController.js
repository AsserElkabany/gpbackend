const Scanner = require('../models/Scanner');

// Add a new network to the scanner collection
const addScanner = async (req, res) => {
    try {
        const { essid, bssid, pwr, enc, channel } = req.body;

        // Optional: check if BSSID already exists
        const exists = await Scanner.findOne({ bssid });
        if (exists) {
            return res.status(400).json({ message: "BSSID already exists" });
        }

        const scanner = new Scanner({ essid, bssid, pwr, enc, channel });
        await scanner.save();
        res.status(201).json(scanner);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

// Get all scanner records
const getScanners = async (req, res) => {
    try {
        const scanners = await Scanner.find();
        res.json(scanners);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

module.exports = { addScanner, getScanners };