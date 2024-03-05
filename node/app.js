
// Check args

if (process.argv.length != 4 || isNaN(process.argv[3]) || process.argv[3] < 0 || process.argv[3] > 65535) {
    console.log('Usage: node app.js <host> <port>');
    process.exit(1);        
}
const HOST = process.argv[2];
const PORT = process.argv[3];

// argument when running the script
const express = require('express');
const bodyParser = require('body-parser');
const esprima = require('esprima');

const app = express();

app.use(bodyParser.text({ limit: '50mb' }));

app.post('/parse', (req, res) => {
    const code = req.body;
    // Check if the code is provided
    if (!code) {
        return res.status(400).send('Code not provided');
    }

    // Perform Esprima processing
    try {
        const ret = esprima.parse(code, {
            range: false,
            comment: false
        });

        //let pretty = JSON.stringify(ret, null, 2);

        // Do something with the parsed code (modify as needed)
        res.status(200).send(ret);
    } catch (error) {
        res.status(418).send(error);
    }
});

app.post('/tokenize', (req, res) => {
    const code = req.body;
    // Check if the code is provided
    if (!code) {
        return res.status(400).send('Code not provided');
    }

    // Perform Esprima processing
    try {
        const ret = esprima.tokenize(code);

        // Do something with the parsed code (modify as needed)
        res.status(200).send(ret);
    } catch (error) {
        res.status(418).send(error);
    }
});

app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

const server = app.listen(PORT, HOST, () => {});

// Handle graceful shutdown
process.on('SIGINT', () => {
    server.close(() => {
        process.exit(0);
    });
});
