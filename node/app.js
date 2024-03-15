
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


        scopes = []


        let outline = estraverse.traverse(ast, {
            enter: function (node, parent) {
                // if parent is not null, has a scope and has an ast
                console.log(parent);
                if (parent && parent.scope && parent.scope.ast) {
                    let scope = dfatool.newGlobalScope()
                    dfatool.buildScope(parent.scope.ast, scope);
                    scopes.push(scope);
                }
                
                if (node.type == 'CallExpression') {
                    if (node.callee.name == 'fetch') {
                        return estraverse.VisitorOption.Skip;
                    }
                }
            },
            leave: function (node, parent) {
                if (node.type == 'CallExpression') {
                    if (node.callee.name == 'fetch') {
                        for (let i = 0; i < scopes.length; i++) {
                            let arg = node.arguments[0].name;
                            if (scopes[i].getDefine(arg)) {
                                let variable = scopes[i].getDefine(arg)
                                let value = variable.inference();
                                if (value) {
                                    console.log()
                                    console.log(value);
                                }
                            }
                        }
                    }
                }
            }
        });

        // Do something with the parsed code (modify as needed)
        res.status(200).send(JSON.stringify(outline, null, 2));
        // print len of scoope
        console.log(scopes.length);
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
