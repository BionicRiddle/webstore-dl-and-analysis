const fs = require('fs');
const esprima = require('esprima');

// Check args
if (process.argv.length == 2 || isNaN(process.argv[2])) {
    console.error('Usage: node pipe.js <NUM>');
    process.exit(1);
}

// argument when running the script
const NUM = process.argv[2];
const pipe_in = '/tmp/pipe_to_node_' + NUM;
const pipe_out = '/tmp/pipe_from_node_' + NUM;
const BUFFER_SIZE = 500000;

if (!fs.existsSync(pipe_in) || !fs.existsSync(pipe_out)) {
    console.error('Pipe does not exist. Exiting.');
    process.exit(1);
}

const read  = fs.createReadStream(pipe_in, { highWaterMark: BUFFER_SIZE });
const write = fs.createWriteStream(pipe_out, { highWaterMark: BUFFER_SIZE });

read.on('readable', () => {
    let data = '';
    let return_string = "";
    let chunk;
    while (null !== (chunk = read.read())) {
        data += chunk.toString();
    }

    try {
        const ret = esprima.parse(data, {
            range: true,
            comment: true
        });
        return_string = JSON.stringify(ret, null, 2);
    } catch (err) {
        return_string = err.toString();
    }
    write.write(return_string);
});

read.on('close', () => {
    process.exit(0);
    // Terminate this process
});

read.on('error', (err) => {
    console.error('Error:', err);
    process.exit(1);
    // Terminate this process on error
});