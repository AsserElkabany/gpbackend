const express = require("express");
const mongoose = require("mongoose");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const os = require("os");

const user_router = require("./routes/user");
const rasberrypi_router = require("./routes/rasberrypi");

const app = express();
const PORT = 3000;

// ===== Middleware =====
app.use(cors({
  origin: true,
  credentials: true
}));

app.use(cookieParser());
app.use(express.json());

// ===== Routes =====
app.use("/api", user_router);
app.use("/api", rasberrypi_router);

// ===== MongoDB Connection =====
const MONGO_URI = "mongodb://127.0.0.1:27017/pentest";

// Function to get local network IP
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (let interfaceName in interfaces) {
    for (let iface of interfaces[interfaceName]) {
      if (iface.family === "IPv4" && !iface.internal) {
        return iface.address;
      }
    }
  }
  return "localhost";
}

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log("✅ MongoDB Connected");

    app.listen(PORT, "0.0.0.0", () => {
      const localIP = getLocalIP();
      console.log("🚀 Server Running");
      console.log(`Local:   http://127.0.0.1:${PORT}`);
      console.log(`Network: http://${localIP}:${PORT}`);
    });

  })
  .catch((err) => {
    console.error("❌ MongoDB connection failed:", err);
  });