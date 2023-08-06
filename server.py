import asyncio
import time
import sys
import logging
import aiohttp
import json
import re

KEY = ''
portdict = {'Bailey': 10000,'Bona': 10001,'Campbell': 10002,'Clark': 10003,'Jaquez': 10004}
adjdict = {
    "Bailey": ["Bona", "Campbell"],
    "Bona": ["Clark", "Bailey","Campbell"],
    "Campbell": ["Bailey", "Bona", "Jaquez"],
    "Clark": ["Jaquez", "Bona"],
    "Jaquez": ["Clark", "Campbell"]
}
localhost = '127.0.0.1'

class PlacesServer:
    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
        self.timedict = dict() #timedict[client] gives recent timestamp
        self.responsedict = dict()
        logging.info(f"log file for server {name}")

    async def parsequeries(self, reader, writer):
        while not reader.at_eof():  # only exits when buffer is non-empty
            data = await reader.readline()
            message = data.decode()
            if message == "":
                continue
            logging.info("{} received: {}".format(self.name, message))
            command = message.split()
            responsemsg = '? ' + message
            if command[0] == 'IAMAT':
                #check valid ISO 6709 location
                if not re.match(r'[+-][0-9]+\.?[0-9]*[+-][0-9]+\.?[0-9]*$', command[2]):
                    logging.info(f'{command[2]} is not valid ISO 6709 notation')
                else:
                    try:
                        diff = time.time() - float(command[3])
                        if diff > 0:
                            responsemsg = f'AT {self.name} {"+"}{diff} {command[1]} {command[2]} {command[3]}'
                        else:
                            responsemsg = f'AT {self.name} {diff} {command[1]} {command[2]} {command[3]}'
                        self.timedict[command[1]] = float(command[3])
                        self.responsedict[command[1]] = responsemsg
                        await self.flood(responsemsg)
                    except:
                        logging.info("couldn't find time diff")
            elif command[0] == 'WHATSAT':
                if command[1] not in self.timedict or int(command[2])<0 or int(command[2])>50 or int(command[3])<0 or int(command[3])>20:
                    logging.info('WHATSAT error -- check bounds or location')
                elif (not re.match(r'^[0-9]+$',command[2])) or (not re.match(r'^[0-9]+$',command[3])):
                    logging.info('arguments after location are not numbers')
                else:
                    radius = float(command[2])*1000
                    bound = command[3]
                    async with aiohttp.ClientSession() as session:
                        coordinates = self.get_coordinates(self.responsedict[command[1]].split()[4])
                        logging.info('calling places api')
                        url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={coordinates}&radius={radius}&key={KEY}'
                        async with session.get(url) as response:
                            result = await response.text()
                        result_object = json.loads(result)
                        logging.info('api return successful')
                        result_object["results"] = result_object["results"][0:min(int(bound),len(result_object['results']))]
                        places = json.dumps(result_object, sort_keys=True, indent=4)
                    responsemsg = "{}\n{}\n\n".format(self.responsedict[command[1]], str(places).rstrip('\n'))
            elif command[0] == 'AT':
                if len(command) != 6:
                    logging.info('incorrect format')
                else:
                    responsemsg = None
                    logging.info('received propagated msg')
                    if command[3] not in self.timedict or float(command[5]) > self.timedict[command[3]]:
                        logging.info(f'propagating client {command[1]}')
                        self.timedict[command[3]] = float(command[5])
                        self.responsedict[command[3]] = message
                        await self.flood(message)
                    else:
                        pass
            if responsemsg != None:
                logging.info(f'response: {responsemsg}')
                writer.write(responsemsg.encode())
                await writer.drain()
        logging.info("close the client socket")
        writer.close()

    async def flood(self, message):
        for neighbor in adjdict[self.name]:
            try:
                reader, writer = await asyncio.open_connection('127.0.0.1', portdict[neighbor])
                logging.info(f'send {message} from {self.name} to {neighbor}')
                writer.write(message.encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except:
                logging.info(f"can't propagate to server {neighbor}")

    def get_coordinates(self, location):
        plusind = location.rfind('+')
        minusind = location.rfind('-')
        if plusind != -1 and plusind != 0:
            return "{},{}".format(location[0:plusind], location[plusind:])
        if minusind != -1 and minusind != 0:
            return "{},{}".format(location[0:minusind], location[minusind:])
        return None

    async def run_forever(self):
        logging.info(f'starting server {self.name}')
        server = await asyncio.start_server(self.parsequeries, self.ip, self.port)
        async with server:
            await server.serve_forever()
        server.close()

def main():
    if len(sys.argv) != 2:
        print('please specify server name\n')
        exit(1)
    if sys.argv[1] not in portdict:
        print(f'{sys.argv[1]} is not a server')
        exit(1)
    logging.basicConfig(level=logging.INFO,format='%(levelname)s: %(message)s',filename=f'{sys.argv[1]}.log',filemode='w')
    s = PlacesServer(sys.argv[1], localhost, portdict[sys.argv[1]])
    asyncio.run(s.run_forever())

if __name__ == '__main__':
    main()