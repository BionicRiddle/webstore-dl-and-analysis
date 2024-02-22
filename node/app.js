const esprima = require('esprima');

process.stdin.on('data', (data) => {
    const input = data.toString().trim(); // Trim to remove newline characters

    // if epmty line, do nothing
    if (input === '') {
        return;
    }

    // Perform actions based on the input
    if (input === '!exit' || input === '!quit' || input === '!q') {
        console.log('Exiting the application.');
        process.exit(); // Terminate the process
    } else {
        // Check if the input is a valid file path
        try {
            // Read the JavaScript code from the specified file
            const ret = esprima.parse(input, {
                range: true,
                comment: true
            });
            console.log(JSON.stringify(ret, null, 2)); // Return the parsed input
        } catch (error) {
            console.error('Error reading or parsing file:', error.message);
        }
    }
    // flush the output buffer
    console.log();
    process.stdout.write('');
});
