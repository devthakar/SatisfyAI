const express = require('express');
const multer = require('multer');
const app = express();
const path = require('path');
const fs = require('fs');

app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});


const uploadsDir = path.join(__dirname, 'uploads');
fs.existsSync(uploadsDir) || fs.mkdirSync(uploadsDir);


const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadsDir);
    },
    filename: function (req, file, cb) {
        cb(null, Date.now() + path.extname(file.originalname));
    }
});
const upload = multer({ storage: storage });
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    console.log("Serving home.html...");
    res.sendFile(path.join(__dirname, 'home.html'));
});

app.post('/upload', upload.single('audioFile'), (req, res) => {
    console.log("POST /upload request received");
    if (!req.file) {
        console.log("No file received");
        res.status(400).send({
          success: false,
          message: "No file uploaded."
        });
    } else {
        const filePath = path.join(uploadsDir, req.file.filename);
        console.log("File received:", req.file.filename);
        console.log("File saved to:", filePath);
        res.send({
          success: true,
          message: "File uploaded successfully.",
          filename: req.file.filename
        });
    }
});


const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
