const Scanner = require('../models/Scanner');
const Handshake = require('../models/Handshake');
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

exports.gethash = async (req, res) => {
    try {
        const { essid, bssid, enc, channel, hash } = req.body;

        // Validate required fields
        if (!essid || !bssid || !enc || !channel || !hash) {
            return res.status(400).json({
                message: "Missing required fields: essid, bssid, enc, channel, hash"
            });
        }

       

        
        const handshake = new Handshake({
            essid: essid.trim(),
            bssid: bssid.trim(),
            enc,
            channel: Number(channel),
            hash,
            status:"uncracked"
        });

       
        const savedHandshake = await handshake.save();

        res.status(201).json({
            message: "Handshake saved successfully",
            data: savedHandshake
        });
    } catch (err) {
        console.error("Handshake save error:", err);

        if (err.name === 'ValidationError') {
            return res.status(400).json({
                message: "Validation failed",
                error: err.message
            });
        }

        if (err.code === 11000) { 
            return res.status(409).json({
                message: "Handshake hash already exists",
                error: err.message
            });
        }

        res.status(500).json({
            message: "Server error while saving handshake",
            error: err.message
        });
    }
};


exports.savePassword = async (req, res) => {
    try {
        const { bssid, password } = req.body;

        if (!bssid || !password) {
            return res.status(400).json({ message: "Missing required fields: bssid and password" });
        }

        const bssidNormalized = bssid.trim();

        const bssidRegex = new RegExp('^' + bssidNormalized.replace(/[:\-]/g, '[:\\-]') + '$', 'i');

        const updated = await Handshake.findOneAndUpdate(
            { bssid: bssidRegex },
            { $set: { password: password, status: 'cracked', crackedAt: new Date() } },
            { new: true }
        );

        if (!updated) {
            return res.status(404).json({ message: 'Handshake with provided BSSID not found' });
        }

        res.status(200).json({ message: 'Password saved successfully', data: updated });
    } catch (err) {
        console.error('Error saving password:', err);
        res.status(500).json({ message: 'Server error while saving password', error: err.message });
    }
};

