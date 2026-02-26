const mongoose = require('mongoose');

const networkScannerSchema = new mongoose.Schema({
    essid: {
        type: String,
        required: true
    },
    bssid: {
        type: String,
        required: true,
        unique: true
    },
    pwr: {
        type: Number,
        required: true
    },
    enc: {
        type: String,
        required: true
    },
    channel: {
        type: Number,
        required: true
    }
}, { timestamps: true }); // timestamps adds createdAt and updatedAt

module.exports = mongoose.model('NetworkScanner', networkScannerSchema);