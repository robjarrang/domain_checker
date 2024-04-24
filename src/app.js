const express = require('express');
const apiRoutes = require('./routes/api');
const app = express();
const path = require('path');

// Define the PORT variable
const PORT = process.env.PORT || 3000;

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, '..', 'public'))); 

// API routes
app.use('/api', apiRoutes);

app.get('/', (req, res) => {
    console.log('Root path hit');
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});  
  
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});