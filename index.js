const express = require("express");
const mongoose = require("mongoose");
const cookieParser = require("cookie-parser");
const cors = require("cors");

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
const MONGO_URI = "mongodb+srv://asser337:nodejs_11.11@cluster0.ceji32w.mongodb.net/pentest?retryWrites=true&w=majority&appName=Cluster0";

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log("MongoDB Connected");

    
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
    });

  })
  .catch((err) => {
    console.error("MongoDB connection failed:", err);
  });