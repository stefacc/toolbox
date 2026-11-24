# wstunnel - WebSocket relay between two clients

A small relay server that connects two clients that can't reach each other directly
(both behind NAT/firewall, but both able to open an outgoing connection to the relay).
Each client opens a WebSocket to the relay, and the relay pipes the two streams
together: whatever one side sends, the other side receives.

```
 source  --ws-->  [ relay :8080 ]  <--ws--  destination
            (streams piped together)
```

Proof of concept, Node.js + Docker.

## How it works

1. The **source** asks the relay for a tunnel to a named destination:
   `POST /api/tunnel  {"source": "<id>", "destination": "mainframe"}` -> returns a `tunnelid`.
2. The **destination** polls `GET /api/tunnel/<its name>` until a tunnel for it exists.
3. Both connect to `ws://<relay>:8080/ws/tunnel/<source|destination>/<tunnelid>/<client id>`.
4. When both sides of a tunnel are connected, the relay pipes them together.

The example clients send base64 `ping` / `pong` messages back and forth.

## Run the local demo

```
docker compose up --build        # or ./compose.sh
```

It starts the relay, a source and a destination (named `mainframe`); in the logs you
see the pipe being created and the ping/pong exchange. Ctrl+C to stop.

## Use a remote relay

Run the relay on a host reachable by both sides:

```
docker build -t wstunnel .
docker run -p 8080:8080 wstunnel
```

and point the clients to it with the `SERVER` variable (default `http://localhost:8080`):

```
cd clients && npm install
SERVER=http://<relay-host>:8080 npm run start-destination
SERVER=http://<relay-host>:8080 npm run start-source
```

## Limitations

- **No authentication and no TLS**: anyone who can reach port 8080 can create or join
  tunnels. Don't expose it on the internet as is; put it behind a reverse proxy with TLS
  and some form of auth, or restrict access with a firewall / VPN.
- Tunnels are kept in memory and never cleaned up; a restart loses them.
- The destination name is matched as is, the first tunnel found wins.
