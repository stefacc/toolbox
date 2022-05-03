spawner = async () => {
    await new Promise((resolve, reject) => {
        let sp = spawn("ls", [], { stdio: 'inherit' });
        sp.on('exit', function (code) {
            resolve();
        });
    });
}

main = async () => {
    await spawner();
}

main();
