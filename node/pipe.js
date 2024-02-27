const esprima = require('esprima');

// node_server_pipe.js
const net = require('net');
const fs = require('fs');
const NUM = 0;
const pipe_in = '/tmp/pipe_to_node_' + NUM;
const pipe_out = '/tmp/pipe_from_node_' + NUM;

// open pipes and read then echo back in reversed

// open pipe for reading
const read = fs.createReadStream(pipe_in, { highWaterMark: 100 });
const write = fs.createWriteStream(pipe_out, { highWaterMark: 100 });

// read from pipe and reverse the string and write to pipe
read.on('data', (data) => {
    const input = data.toString().trim(); // Trim to remove newline characters
    console.log('input: ', input);

    // reverse input and write to pipe
    write.write(input.split("").reverse().join("") + '\n');

    
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
