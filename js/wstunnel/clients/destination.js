const WebSocket = require('ws');
const axios = require('axios');
// Relay server address, e.g. http://localhost:8080 (the ws:// URL is derived from it)
const SERVER = process.env.SERVER || 'http://localhost:8080';
const WS_SERVER = SERVER.replace(/^http/, 'ws');
const id = 'mainframe' //require("uuid").v4();
console.log(`Hi, I'm ${id}`);

function main() {
    axios.get(`${SERVER}/api/tunnel/${id}`)
        .then((response) => {
            console.log('Response:', response.data);
            clearTimeout(timer)
            setTimeout(() => {
                startws(response.data['tunnelid'])
            }, 2000);
        })
        .catch((error) => {
            console.error('Error:', error.response.status);
        });
}

timer = setInterval(() => {
    main()
}, 2000);

function startws(tunnelid) {
    const ws = new WebSocket(`${WS_SERVER}/ws/tunnel/destination/${tunnelid}/${id}`)
    messageB64 = Buffer.from('pong', 'utf8').toString('base64');
    ws.on('message', function message(data) {
        console.log('Received from server base64:', data.toString());
        console.log('Received from server:', Buffer.from(data.toString(), 'base64').toString());
        setTimeout(() => { ws.send(messageB64) }, 1000);
    });

    ws.on('open', function open() {
        console.log('Connected to the server');
    });

    ws.on('close', function close() {
        console.log('Disconnected from the server');
    });

    ws.on('error', function error(err) {
        console.error('WebSocket error:', err);
    });

}
