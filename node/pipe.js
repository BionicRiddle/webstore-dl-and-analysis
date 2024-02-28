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

// open pipe for reading
const read = fs.createReadStream(pipe_in, { highWaterMark: 100000 });
const write = fs.createWriteStream(pipe_out, { highWaterMark: 100000 });

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


// process.stdin.on('data', (data) => {
//     const input = data.toString().trim(); // Trim to remove newline characters

//     // if epmty line, do nothing
//     if (input === '') {
//         return;
//     }

//     // Perform actions based on the input
//     if (input === '!exit' || input === '!quit' || input === '!q') {
//         console.log('Exiting the application.');
//         process.exit(); // Terminate the process
//     } else {
//         // Check if the input is a valid file path
//         try {
//             // Read the JavaScript code from the specified file
//             const ret = esprima.parse(input, {
//                 range: true,
//                 comment: true
//             });
//             console.log(JSON.stringify(ret, null, 2)); // Return the parsed input
//         } catch (error) {
//             console.error('Error reading or parsing file:', error.message);
//         }
//     }
//     // flush the output buffer
//     console.log();
//     // send eof to the input stream
//     process.stdin.emit('end');
// });
