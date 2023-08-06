# Google-Places-Proxy-Prototype
Adapted from https://web.cs.ucla.edu/classes/winter23/cs131/hw/pr.html

This is a parallelizable proxy for the Google Places API, using Python's asyncio networking library.
This prototype consists of five servers with server IDs 'Bailey', 'Bona', 'Campbell', 'Clark', 'Jaquez' that communicate to each other bidirectionally.

Each server accepts TCP connections from clients, who can send their location to the server using this format:
IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503

Its operands are the client ID (in this case, kiwi.cs.ucla.edu), the latitude and longitude in decimal degrees using ISO 6709 notation, and the client's time, in POSIX time.
The server will respond with a message on reception.

Clients can also query for information about places near other clients' locations, with a query using this format:
WHATSAT kiwi.cs.ucla.edu 10 5

The arguments to a WHATSAT message are the name of another client (e.g., kiwi.cs.ucla.edu), a radius (in kilometers) from the client (e.g., 10), 
and an upper bound on the amount of information to receive from Places data within that radius of the client (e.g., 5).
The server responds with a AT message in the same format as before, giving the most recent location reported by the client, along with the server that it talked to and the time the server did the talking. 
Following the AT message is a JSON-format message, exactly in the same format that Google Places gives for a Nearby Search request.
