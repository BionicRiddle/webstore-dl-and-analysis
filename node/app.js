// Check args
if (process.argv.length == 2 || isNaN(process.argv[2])) {
    console.error('Usage: node pipe.js <NUM>');
    process.exit(1);
}

const esprima = require('esprima');
const fs = require('fs');

// argument when running the script
const NUM = process.argv[2];
const pipe_in = '/tmp/pipe_to_node_' + NUM;
const pipe_out = '/tmp/pipe_from_node_' + NUM;

// Check if file already exist
if (!fs.existsSync(pipe_in) || !fs.existsSync(pipe_out)) {
    console.error('Pipe does not exist. Exiting.');
    process.exit(1);
}

// open pipe for reading
const read  = fs.createReadStream(  pipe_in,    { highWaterMark: 500000 });
const write = fs.createWriteStream( pipe_out,   { highWaterMark: 500000 });

// read from pipe and reverse the string and write to pipe
read.on('data', (data) => {
    const input = data.toString();
    
    const ret = esprima.parse(input, {
        range: true,
        comment: true
    });

    // reverse input and write to pipe
    write.write(JSON.stringify(ret, null, 2));
})