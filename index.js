const express = require("express");
const mongoose = require("mongoose");
const cookieParser = require('cookie-parser');
const cors = require('cors');
const user_router = require("./routes/user");
const scanner_router = require("./routes/scanner");

const app = express();
const PORT = 3000;

// Middleware
app.use(cors({
  origin: true,
  credentials: true
}));
app.use(cookieParser());
app.use(express.json());

// Routes
app.use('/api', user_router);
app.use('/api', scanner_router);

const mongoURI = "mongodb+srv://asser337:nodejs_11.11@cluster0.ceji32w.mongodb.net/pentest?retryWrites=true&w=majority&appName=Cluster0";

mongoose.connect(mongoURI)
    .then(() => console.log("MongoDB connected successfully to pentest database"))
    .catch(err => console.error("MongoDB connection error:", err));

// Start server
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));