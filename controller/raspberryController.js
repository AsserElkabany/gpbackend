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

        // Optional: basic structure validation for each item
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

       

        // Create new handshake document
        const handshake = new Handshake({
            essid: essid.trim(),
            bssid: bssid.trim(),
            enc,
            channel: Number(channel),
            hash,
            status:"uncracked"
        });

        // Save to database
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

        if (err.code === 11000) { // Mongo duplicate key error
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

// ==================== WPA/WPA2/WPA3 PBKDF2 Brute Force ====================

function generatePBKDF2(password, ssid, enc) {
    // WPA/WPA2 use PBKDF2-HMAC-SHA1 with 4096 iterations
    // WPA3 can use up to 48000 iterations - we'll use a reasonable default
    const iterations = enc === 'WPA3' ? 48000 : 4096;
    
    return new Promise((resolve) => {
        crypto.pbkdf2(password, ssid, iterations, 32, 'sha1', (err, derivedKey) => {
            if (err) {
                resolve(null);
            } else {
                resolve(derivedKey.toString('hex'));
            }
        });
    });
}

function createBruteWorker(workerIndex, totalWorkers, ssid, targetHash, enc, wordlist) {
    return new Promise((resolve) => {
        const worker = new Worker(
            `
            const crypto = require('crypto');
            const { parentPort, workerData } = require('worker_threads');
            const { workerIndex, totalWorkers, ssid, targetHash, enc, wordlist } = workerData;
            
            function generatePBKDF2(password, ssid, enc) {
                const iterations = enc === 'WPA3' ? 48000 : 4096;
                return new Promise((resolve) => {
                    crypto.pbkdf2(password, ssid, iterations, 32, 'sha1', (err, derivedKey) => {
                        if (err) resolve(null);
                        else resolve(derivedKey.toString('hex'));
                    });
                });
            }
            
            async function bruteWorker() {
                for (let i = workerIndex; i < wordlist.length; i += totalWorkers) {
                    const password = wordlist[i].trim();
                    const hash = await generatePBKDF2(password, ssid, enc);
                    
                    if (hash === targetHash) {
                        parentPort.postMessage({found: true, password});
                        return;
                    }
                }
                parentPort.postMessage({found: false});
            }
            
            bruteWorker();
            `,
            { eval: true, workerData: { workerIndex, totalWorkers, ssid, targetHash, enc, wordlist } }
        );

        worker.on('message', msg => {
            if (msg.found) {
                resolve(msg.password);
            } else {
                resolve(null);
            }
            worker.terminate();
        });

        worker.on('error', () => {
            resolve(null);
            worker.terminate();
        });
    });
}

exports.bruteForceWPA = async (req, res) => {
    try {
        const { id } = req.params;
        
        if (!id) {
            return res.status(400).json({ message: 'Handshake ID required' });
        }

        // Find handshake in database
        const handshake = await Handshake.findById(id);
        if (!handshake) {
            return res.status(404).json({ message: 'Handshake not found' });
        }

        // Only for WPA, WPA2, WPA3
        if (!['WPA', 'WPA2', 'WPA3'].includes(handshake.enc)) {
            return res.status(400).json({ message: `Encryption type ${handshake.enc} not supported for brute force` });
        }

        const { essid, hash: targetHash, enc } = handshake;

        // Common wordlist - in production, load from file
        const commonPasswords = [
            'password', '123456', '12345678', '1234567890', 'qwerty', 'abc123',
            'monkey', '1q2w3e4r', 'letmein', 'trustno1', 'dragon', '123123',
            'admin', 'password123', '123456789', '000000', 'security', '666666',
            'mypassword', 'iloveyou', 'welcome', 'batman', 'starwars', 'apple',
            'google', 'facebook', 'twitter', 'linkedin', 'instagram', 'netflix',
            'amazon', 'microsoft', 'windows', 'linux', 'ubuntu', 'debian',
            'raspberry', 'pi', 'test', 'demo', 'user', 'root'
        ];

        res.status(200).json({ message: 'Brute force started', id, handshakeInfo: { essid, enc } });

        // Run brute force in background and update DB when done
        (async () => {
            const cpus = Math.min(os.cpus().length, 4); // limit to 4 workers max
            const workerPromises = [];

            for (let i = 0; i < cpus; i++) {
                workerPromises.push(
                    createBruteWorker(i, cpus, essid, targetHash, enc, commonPasswords)
                );
            }

            // Race: first worker to find it wins
            const crackedPassword = await Promise.race(workerPromises);

            if (crackedPassword) {
                // Update database with cracked password
                await Handshake.findByIdAndUpdate(id, {
                    status: 'cracked',
                    crackedPassword: crackedPassword,
                    crackedAt: new Date()
                });
                console.log(`✓ Handshake ${id} cracked: ${crackedPassword}`);
            } else {
                // Update as failed
                await Handshake.findByIdAndUpdate(id, {
                    status: 'failed',
                    failedAt: new Date()
                });
                console.log(`✗ Handshake ${id} not cracked with common passwords`);
            }
        })();

    } catch (err) {
        console.error('Brute force error:', err);
        return res.status(500).json({ message: 'Server error', error: err.message });
    }
};


