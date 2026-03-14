const NmapScan = require('../models/NmapScan');

exports.saveNmapOutput = async (req, res) => {
    try {
        const { bssid, essid, timestamp, host_count, hosts, raw_output } = req.body;

        if (!raw_output || host_count === undefined || !hosts) {
            return res.status(400).json({
                message: "Required fields: raw_output, host_count, hosts are missing"
            });
        }

        const nmapScan = new NmapScan({
            bssid,
            essid,
            timestamp: timestamp ? new Date(timestamp) : new Date(),
            host_count,
            hosts,
            raw_output: raw_output.substring(0, 4000) // Ensure max 4000 chars
        });

        const savedScan = await nmapScan.save();

        res.status(201).json({
            message: "Nmap output saved successfully",
            scan: savedScan
        });

    } catch (error) {
        console.error('Error saving nmap output:', error);
        res.status(500).json({
            message: "Error saving nmap output",
            error: error.message
        });
    }
};

exports.getNmapScans = async (req, res) => {
    try {
        const scans = await NmapScan.find().sort({ createdAt: -1 });
        res.status(200).json(scans);
    } catch (error) {
        console.error('Error fetching nmap scans:', error);
        res.status(500).json({
            message: "Error fetching nmap scans",
            error: error.message
        });
    }
};