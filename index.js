const express = require("express");
const mongoose = require("mongoose");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const os = require("os");

const user_router = require("./routes/user");
const rasberrypi_router = require("./routes/rasberrypi");

const app = express();
const PORT = 12345;

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

// Function to get REAL LAN IPv4 (ignores VirtualBox/Docker)
function getLANIP() {
  const interfaces = os.networkInterfaces();

  for (let name of Object.keys(interfaces)) {
    for (let iface of interfaces[name]) {

      if (
        iface.family === "IPv4" &&
        !iface.internal &&
        (
          iface.address.startsWith("192.168.") ||
          iface.address.startsWith("10.") ||
          iface.address.startsWith("172.")
        ) &&
        !iface.address.startsWith("192.168.56.") // ignore VirtualBox
      ) {
        return iface.address;
      }
    }
  }

  return "127.0.0.1";
}

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log("✅ MongoDB Connected");

    const LAN_IP = getLANIP();

    app.listen(PORT, LAN_IP, () => {
      console.log("🚀 Server Running");
      console.log(`Local:   http://127.0.0.1:${PORT}`);
      console.log(`Network: http://${LAN_IP}:${PORT}`);
    });

  })
  .catch((err) => {
    console.error("❌ MongoDB connection failed:", err);
  });