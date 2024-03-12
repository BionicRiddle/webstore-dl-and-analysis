
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
const dfatool = require('dfatool');

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

app.post('/flow', (req, res) => {
    const code = req.body;
    // Check if the code is provided
    if (!code) {
        return res.status(400).send('Code not provided');
    }

    // Perform Esprima processing
    // try {
        const ast = esprima.parse(code, {
            loc: true
        });

        let globalScope = dfatool.newGlobalScope();
        dfatool.buildScope(ast, globalScope);

        globalScope.initialize();
        globalScope.derivation();

        var outline = {};

        // Iterate all the defined variables and inference its value
        for(var name in globalScope._defines){
            var variable = globalScope._defines[name];
            var value = variable.inference();
            if( value ){
                outline[variable.name] = value.toJSON();
            }
        }

        // Do something with the parsed code (modify as needed)
        res.status(200).send(JSON.stringify(outline, null, 2));
    // } catch (error) {
    //     res.status(418).send(JSON.stringify(error, null, 2));
    // }
});

app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

const server = app.listen(PORT, HOST, () => {
    console.log(`Server running at http://${HOST}:${PORT}/`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down gracefully...');
    server.close(() => {
        console.log('Closed out remaining connections');
        process.exit(0);
    });
});
