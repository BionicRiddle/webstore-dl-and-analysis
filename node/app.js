const fs = require('fs');
const esprima = require('esprima');

let count = 0;

// Check args
if (process.argv.length == 2 || isNaN(process.argv[2])) {
    console.error('Usage: node pipe.js <NUM>');
    process.exit(1);
}

// argument when running the script
const NUM = process.argv[2];
const pipe_in = '/tmp/pipe_to_node_' + NUM;
const pipe_out = '/tmp/pipe_from_node_' + NUM;
const BUFFER = 500000;

if (!fs.existsSync(pipe_in) || !fs.existsSync(pipe_out)) {
    console.error('Pipe does not exist. Exiting.');
    process.exit(1);
}

// Create a buffer 
let data = '';


const read  = fs.createReadStream(pipe_in, { highWaterMark: BUFFER });

read.on('readable', () => { 
    let chunk; 

    // Using while loop and calling 
    // read method 
    while (null !== (chunk = read.read())) { 

        let dataa = chunk.toString();

        console.log('Received data:', dataa);
        // Store the data in a buffer
        data += dataa;
    }

    const ret = esprima.parse(data, {
        range: true,
        comment: true
    });

    const write = fs.createWriteStream(pipe_out, { highWaterMark: BUFFER });
    write.write(JSON.stringify(ret, null, 2));

    // send null to write pipe
    write.end(null);

    // Clear the buffer
    data = '';

    count += 1;
    console.log('Processed:', count);

    // Empty the buffer

});

read.on('close', () => {
    console.log('Named pipe closed');
    keep_alive = false;
    // Terminate this process
});

read.on('error', (err) => {
    console.error('Error:', err);
    // Terminate this process on error

});



// // Check if file already exist
// if (!fs.existsSync(pipe_in) || !fs.existsSync(pipe_out)) {
//     console.error('Pipe does not exist. Exiting.');
//     process.exit(1);
// }

// while (true) {
//     // open pipe for reading
//     const read  = fs.createReadStream(  pipe_in,    { highWaterMark: 500000 });
//     const write = fs.createWriteStream( pipe_out,   { highWaterMark: 500000 });

//     // read from pipe and reverse the string and write to pipe
//     read.on('data', (data) => {
//         const input = data.toString();
        
//         const ret = esprima.parse(input, {
//             range: true,
//             comment: true
//         });

//         // reverse input and write to pipe
//         write.write(JSON.stringify(ret, null, 2));
//     })

//     // close the pipe
//     console.log('Closing the pipe.');
// }

// process.stdin.on('data', (data) => {
//     const input = data.toString().trim(); // Trim to remove newline characters

//     // if epmty line, do nothing
//     if (input === '') {
//         return;
//     }

//     // Perform actions based on the input
//     if (input === 'exit' || input === 'quit' || input === 'q') {
//         console.log('Exiting the application.');
//         process.exit(); // Terminate the process
//     }
// });