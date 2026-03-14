const mongoose = require('mongoose');

const nmapScanSchema = new mongoose.Schema({
    bssid: {
        type: String,
        required: false
    },
    essid: {
        type: String,
        required: false
    },
    timestamp: {
        type: Date,
        required: true
    },
    host_count: {
        type: Number,
        required: true
    },
    hosts: [{
        ip: {
            type: String,
            required: true
        },
        mac: {
            type: String,
            required: false
        }
    }],
    raw_output: {
        type: String,
        required: true,
        maxlength: 4000
    }
}, { timestamps: true });

module.exports = mongoose.model('NmapScan', nmapScanSchema);