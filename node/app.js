
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
const estraverse = require('estraverse');
const escope = require('escope');

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

    console.log();

    // Perform Esprima processing
    // try {

        let ast = esprima.parse(code, {
            range: false,
            comment: false,
            loc : true
        });

        let scopeManager = escope.analyze(ast);

        let currentScope = scopeManager.acquire(ast);   // global scope
        estraverse.traverse(ast, {
            enter: function(node, parent) {
                // do stuff

                if (/Function/.test(node.type)) {
                    currentScope = scopeManager.acquire(node);  // get current function scope
                }

                let arg = null;
            
                if (node.type === 'CallExpression') {
                    if (node.callee.name === 'fetch') {
                        arg = node.arguments[0].name;
                        
                        let vars = currentScope.variables;
                        // find "arg" in the current scope
                        for (let i = 0; i < vars.length; i++) {
                            if (vars[i].name === arg) {
                                //console.log('Found ' + arg + ' in scope');
                                console.log(vars[i]);
                                let r = currentScope
                            }
                        }
                        
                    }
                }
            },
            leave: function(node, parent) {
                if (/Function/.test(node.type)) {
                    currentScope = currentScope.upper;  // set to parent scope
                }
                
                // do stuff
            }
        });

        //console.log(scopeManager);

        outline = scopeManager

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
