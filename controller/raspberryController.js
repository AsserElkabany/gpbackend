const Scanner = require('../models/Scanner');
const crypto = require('crypto');
const os = require('os');
const { Worker } = require('worker_threads');
const fs = require('fs');
const path = require('path');



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

      
        const validNetworks = networks.map(net => {
            const { essid, bssid, pwr, enc, channel } = net;

            
            if (!bssid) {
                throw new Error("Each network must have a bssid");
            }

            return {
                essid: essid || null,    
                bssid: bssid.trim(),      
                pwr: Number(pwr) || -100, 
                enc: enc || "Unknown",
                channel: Number(channel) || 0
            };
        });

       
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

        if (err.code === 11000) { 
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


exports.getScanners = async (req, res) => {
    try {
        const scanners = await Scanner.find();
        res.json(scanners);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};





exports.savePassword = async (req, res) => {
    try {
        const { bssid, password } = req.body;

        if (!bssid || !password) {
            return res.status(400).json({ 
                message: "Missing required fields: bssid and password" 
            });
        }

        const bssidNormalized = bssid.trim();

        // Case-insensitive BSSID match
        const bssidRegex = new RegExp(
            '^' + bssidNormalized.replace(/[:\-]/g, '[:\\-]') + '$',
            'i'
        );

        // Update scanner entry locally only
        const updated = await Scanner.findOneAndUpdate(
            { bssid: bssidRegex },
            { 
                $set: { 
                    password: password,
                    crackedAt: new Date()
                } 
            },
            { new: true }
        );

        if (!updated) {
            return res.status(404).json({ 
                message: 'Scanner entry with provided BSSID not found' 
            });
        }

        return res.status(200).json({ 
            message: 'Password saved successfully', 
            data: updated 
        });

    } catch (err) {
        console.error('Error saving password:', err);
        return res.status(500).json({ 
            message: 'Server error while saving password', 
            error: err.message 
        });
    }
};