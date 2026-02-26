const Scanner = require('../models/Scanner');

// Add a new network to the scanner collection
exports.addScanners = async (req, res) => {
    try {
        const networks = req.body; 

        
        if (!Array.isArray(networks)) {
            return res.status(400).json({ 
                message: "Request body must be an array of networks" 
            });
        }

        if (networks.length === 0) {
            return res.status(400).json({ 
                message: "No networks provided" 
            });
        }

        // Optional: basic structure validation for each item
        const validNetworks = networks.map(net => {
            const { essid, bssid, pwr, enc, channel } = net;

            
            if (!bssid) {
                throw new Error("Each network must have a bssid");
            }

            return {
                essid: essid || null,     // allow empty ESSID
                bssid: bssid.trim(),      // usually good to normalize
                pwr: Number(pwr) || -100, // default to very weak if missing
                enc: enc || "Unknown",
                channel: Number(channel) || 0
            };
        });

        // Bulk insert - much faster than saving one by one
        const insertedScanners = await Scanner.insertMany(validNetworks, {
            ordered: false,           
           
        });

        res.status(201).json({
            message: `Successfully added ${insertedScanners.length} networks`,
            count: insertedScanners.length,
           
        });

    } catch (err) {
        console.error("Bulk scanner insert error:", err);

        if (err.name === 'ValidationError') {
            return res.status(400).json({
                message: "Validation failed",
                error: err.message
            });
        }

        if (err.code === 11000) { // Mongo duplicate key error
            return res.status(409).json({
                message: "Some BSSIDs already exist (duplicates skipped)",
                error: err.message
            });
        }

        res.status(500).json({
            message: "Server error while saving networks",
            error: err.message
        });
    }
};

// Get all scanner records
exports.getScanners = async (req, res) => {
    try {
        const scanners = await Scanner.find();
        res.json(scanners);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

