const websocketStream = require('websocket-stream');
const ws = require("ws");
const url = require('url');
const http = require('http');
const express = require('express');
const bodyParser = require('body-parser');

const app = express();
const apiRouter = express.Router();

app.use(bodyParser.json());
app.use('/api', apiRouter);

const server = http.createServer(app);
const wsServer = new ws.Server({ server });

app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

server.listen(8080, () => {
    console.log('Server listening on port 8080');
});

let mem = {}

apiRouter.post('/tunnel', (req, res) => {
    console.log('Received a new message:', req.body);
    const tunnelid = require("uuid").v4();
    const { source, destination } = req.body;
    mem[tunnelid] = { tunnelid: tunnelid, source: { name: source, connected: false }, destination: { name: destination, connected: false } };
    console.log('New tunnel saved:', mem[tunnelid]);
    res.end(JSON.stringify(mem[tunnelid]));
});

apiRouter.get('/tunnel/:destination', (req, res) => {
    const memArray = Object.values(mem);
    let tunnel = memArray.find((item) => item.destination.name === req.params.destination)
    console.log(tunnel);
    if (tunnel === undefined)
        res.status(500).end();
    else
        res.end(JSON.stringify(tunnel));
});

function handleClientDisconnection(id) {
    console.log(`${id} disconnected.`);
    //delete clients[id]
}
wsServer.on("connection", function handleNewConnection(ws, req) {
    console.log("Received a new connection");
    const pathsplit = url.parse(req.url, true).pathname.split('/');
    const type = pathsplit[3]
    const tunnelid = pathsplit[4]
    const client = pathsplit[5]
    ws.on("close", () => handleClientDisconnection(client));
    const stream = websocketStream(ws);
    try {
        mem[tunnelid][type]['ws'] = ws
        mem[tunnelid][type]['stream'] = stream
        mem[tunnelid][type]['connected'] = true
        console.log(`${client} connected on server.`);
        console.log(`${client} streamed.`);
        if (mem[tunnelid]['source']['connected'] && mem[tunnelid]['destination']['connected']){
            const s = mem[tunnelid]['source']
            const d = mem[tunnelid]['destination']
            s.stream.pipe(d.stream).pipe(s.stream);
            console.log(`Pipe between ${mem[tunnelid]['source']['name']} and ${mem[tunnelid]['destination']['name']} is created on ${mem[tunnelid]['tunnelid']}`);
        }
    } catch(e) {
        console.error(e)
        ws.close();
        console.log(`${client} purged.`);
    }

})
