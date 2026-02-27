const mongoose = require('mongoose');

const handshakeSchema = new mongoose.Schema(
  {
    essid: {
      type: String,
      required: true,
      trim: true,
    },
    bssid: {
      type: String,
      required: true,
      trim: true,
      match: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, 
    },
    enc: {
      type: String,
      required: true,
      enum: ['WEP', 'WPA', 'WPA2', 'WPA3', 'Open'],
    },
    channel: {
      type: Number,
      required: true,
      min: 1,
      max: 165,
    },
    hash: {
      type: String,
      required: true,
      unique: true,
    },
    status:{
        type: String,
        required:true,
    }
  },
  { timestamps: true }
);

module.exports = mongoose.model('Handshake', handshakeSchema);
