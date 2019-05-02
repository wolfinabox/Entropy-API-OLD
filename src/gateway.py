#========================================================#
# File:   gateway.py - Handles websocket connection to Discord
# Author: wolfinabox
# GitHub: https://github.com/wolfinabox/Entropy-API
#========================================================#
import websockets
import threading
import asyncio
import json
from threading import Timer
import colorama

from .wolfinaboxutils.formatting import truncate
from .utils import get_os
from .cache import *
colorama.init(autoreset=True)

# Temp for debugging
COLOR_EVENT = colorama.Style.DIM+colorama.Fore.CYAN
COLOR_SEND = colorama.Style.BRIGHT+colorama.Fore.MAGENTA
COLOR_RECV = colorama.Style.BRIGHT+colorama.Fore.GREEN
COLOR_WARN = colorama.Style.BRIGHT+colorama.Fore.YELLOW
COLOR_ERROR = colorama.Style.BRIGHT+colorama.Fore.RED
COLOR_RESET = colorama.Style.RESET_ALL


class Gateway(object):
    """
    A WebSocket Gateway connection to Discord
    """
    opcodes = {
        0: 'DISPATCH',
        1: 'HEARTBEAT',
        2: 'IDENTIFY',
        3: 'STATUS UPDATE',
        4: 'VOICE STATUS UPDATE',
        6: 'RESUME',
        7: 'RECONNECT',
        8: 'REQUEST GUILD MEMBERS',
        9: 'INVALID SESSION',
        10: 'HELLO',
        11: 'HEARTBEAT ACK'
    }

    def __init__(self, token: str, gateway_url: str, loop):
        self.loop = loop
        self.token = token
        self.session_id = None
        self.gateway_url = gateway_url
        self.heartbeat_ms = 0
        self.heartbeat_stop = threading.Event()
        self.heartbeat_acked = True
        self.last_heartbeat_s = None
        self.ws: websockets.WebSocketClientProtocol = None

    async def setup(self):
        """
        Setup the gateway
        """
        self.ws = await websockets.connect(self.gateway_url, compression=None)
        # QUESTIONABLE?
        # IF I AWAIT THIS, IT KEEPS RUNNING, BUT "BLOCKS"
        # IF I DON'T AWAIT THIS, LOOP ONLY RUNS ONCE
        await asyncio.ensure_future(self._run())

    async def _send(self, data:dict):
        """
        Send data over the gateway.\n
        `data` A dictionary to be send. Should contain at least:\n
        {op,d}
        """
        # {data}')
        print(COLOR_SEND +
              f'SENT: op[{data["op"]}] ({self.opcodes[data["op"]]})')
        if type(data) != str:
            data = json.dumps(data)
        await self.ws.send(data)

    async def _handle_event(self, data:dict):
        """
        Handle an event sent from the Discord API\n
        An event is any packet sent with opcode 0\n
        `data` The whole packet sent
        """
        print(COLOR_EVENT+f'GOT EVENT: {data["t"]}')

        # Ready event
        async def ready_t():
            # json.dump(data,open('READY_EXAMPLE.json','w'),indent=4)
            self.session_id = data['d']['session_id']
            cache_put('clientinfo', data['d'])

        # Message_Create
        async def message_create_t():
            NotImplemented

        async def unknown_t():
            print(COLOR_WARN+f'Unhandled event "{data["t"]}"!')
        handlers = {
            'READY': ready_t,
            'MESSAGE_CREATE': message_create_t
        }
        await handlers.get(data['t'], unknown_t)()

    async def _handle_message(self, data: dict):
        # truncate(data,125,"...")}')
        print(
            '\n'+COLOR_RECV+f'RECEIVED: op[{data["op"]}] ({self.opcodes.get(data["op"],"UNKNOWN")})'+(f', s[{data["s"]}]' if data["s"] is not None else ""))
        # Opcode handler functions

        # Dispatch (most events)
        async def op0():
            await self._handle_event(data)

        # Hello
        async def op10():
            self.heartbeat_ms = data['d']['heartbeat_interval']
            print(f'Heartbeating every {self.heartbeat_ms}ms!')
            self._heartbeat(self.heartbeat_stop)
            await self._identify()

        # Heartbeat ACK
        async def op11():
            self.heartbeat_acked = True

        async def unknown_op():
            print(COLOR_WARN+f'Unhandled opcode "{data["op"]}"!')
        # Handlers for each opcode
        handlers = {
            0: op0,
            10: op10,
            11: op11
        }
        self.last_heartbeat_s = data['s']
        await handlers.get(data['op'], unknown_op)()

    async def _run(self):
        """
        Run the gateway (called automatically)
        """
        while not self.ws.closed:
            res = await self.ws.recv()
            await self._handle_message(json.loads(res))

    def _heartbeat(self, heartbeat_stop:threading.Event):
        """
        Heartbeat
        """
        if not self.heartbeat_acked:
            print(COLOR_ERROR+'No heartbeat ACK received!')
            return
        self.heartbeat_acked = False
        asyncio.ensure_future(self._send({
            'op': 1,
            'd': self.last_heartbeat_s  # if self.last_heartbeat_s is not None else 'null'
        }), loop=self.loop)
        if not heartbeat_stop.is_set():
            threading.Timer(float(self.heartbeat_ms)/1000.00,
                            self._heartbeat, [heartbeat_stop]).start()

    async def _identify(self):
        """
        Identify
        """
        await self._send({
            'op': 2,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': get_os(),
                    '$browser': 'entropy',
                    '$device': 'entropy'
                }
            }
        })
