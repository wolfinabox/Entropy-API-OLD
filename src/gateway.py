#========================================================#
# File:   gateway.py - Handles websocket connection to Discord
# Author: wolfinabox
# GitHub: https://github.com/wolfinabox/Entropy-API
#========================================================#
from .cache import *
from .utils import get_os
from .wolfinaboxutils.formatting import truncate
import websockets
from socket import gaierror
import threading
import asyncio
import json
from threading import Timer
import random
import logging
logger = logging.getLogger('discord')


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

    # Amount of time (in s) to sleep between _resume attempts upon disconnection
    sleep_resume = 5

    def __init__(self, token: str, gateway_url: str, loop):
        # Data
        self.session_id = None
        self.token = token
        self.gateway_url = gateway_url
        self.last_sequence = None
        self.identified = False
        # Heartbeat Stuff
        self.heartbeat_ms = 0
        self.heartbeat_acked = True
        self.heartbeat_stop = threading.Event()
        self.heartbeat_timer: threading.Timer = None
        # Structure
        self.loop = loop
        self.ws: websockets.WebSocketClientProtocol = None
        self.send_queue = []

    async def setup(self):
        """
        Setup the gateway
        """
        self.ws = await websockets.connect(self.gateway_url, compression=None)
        asyncio.ensure_future(self._run())

    async def disconnect(self, reason: str = ''):
        """
        Disconnect the gateway.\n
        `reason` The reason to send for the disconnection. Default empty.
        """

        logger.warn('Gateway disconnected! ' +
                    (f'Reason: {reason}' if reason else ''))
        self.heartbeat_timer.cancel()
        await self.ws.close(reason=reason)

    async def _send(self, data: dict):
        """
        Send data over the gateway.\n
        `data` A dictionary to be send. Should contain at least:\n
        {op,d}
        """
        # If the websocket is not open
        if self.ws is None or self.ws.closed:
            logger.warn(f'Send Queued: {data}')
            self.send_queue.append(data)
            return
        logger.debug(f'SENT: op[{data["op"]}] ({self.opcodes[data["op"]]})')
        if type(data) != str:
            data = json.dumps(data)

        # Try to send the data
        try:
            await self.ws.send(data)
        # If the websocket wasn't able to send (connection closed, probably)
        except websockets.ConnectionClosed as e:
            logger.warn(f'Send Queued: {data}')
            self.send_queue.append(data)
            logger.error(f'Gateway closed! Code = {e.code} ({e.reason})')
            await self.disconnect()
            asyncio.ensure_future(self._resume())

    async def _handle_event(self, data: dict):
        """
        Handle an event sent from the Discord API\n
        An event is any packet sent with opcode 0\n
        `data` The whole packet sent
        """
        logger.debug(f'GOT EVENT: {data["t"]}')

        # EVENTS
        # Ready event
        async def ready_t():
            # json.dump(data,open('READY_EXAMPLE.json','w'),indent=4)
            self.session_id = data['d']['session_id']
            cache_put('clientinfo', data['d'])
            test=cache_get('clientinfo.notes.560021188861100064')
            

        async def resume_t():
            logger.debug('Successfully resumed')
        # Message_Create
        # async def message_create_t():
        #     NotImplemented

        async def unknown_t():
            logger.warn(f'Unhandled event "{data["t"]}"!')

        handlers = {
            'READY': ready_t,
            'RESUMED': resume_t
            # 'MESSAGE_CREATE': message_create_t
        }
        await handlers.get(data['t'], unknown_t)()

    async def _handle_message(self, data: dict):
        """
        Handle a message sent from the Discord API.\n
        `data` The data received through the gateway.
        """
        logger.debug(f'RECEIVED: op[{data["op"]}] ({self.opcodes.get(data["op"],"UNKNOWN")})'+(
            f', s[{data["s"]}]' if data["s"] is not None else ""))

        # OPCODES
        # Dispatch (most events)
        async def op0():
            await self._handle_event(data)

        # Heartbeat Request
        async def op1():
            await self._heartbeat(onetime=True)
        
        #Reconnect Request
        async def op7():
            logger.error(f'Gateway closed! (API requested reconnect)')
            await self.disconnect()
            self.identified=False
            asyncio.ensure_future(self._resume())
            
        
        # Invalid Session
        async def op9():
            # If session is resumable
            if data['d']:
                # temp
                await asyncio.sleep(random.randint(1, 5))
                await self._identify()
            else:
                # TEMPORARY (obviously)
                logger.error('Cannot resume from INVALID SESSION! PANIC!!!!!')
                raise ConnectionError('Cannot resume from INVALID SESSION')

        # Hello
        async def op10():
            self.heartbeat_ms = data['d']['heartbeat_interval']
            logger.debug(f'Heartbeating every {self.heartbeat_ms}ms!')
            self._heartbeat(self.heartbeat_stop)
            # Only identify if new connection!
            if not self.identified:
                await self._identify()

        # Heartbeat ACK
        async def op11():
            self.heartbeat_acked = True

        async def unknown_op():
            logger.warn(f'Unhandled opcode "{data["op"]}"!')

        # Handlers for each opcode
        handlers = {
            0: op0,
            1:op1,
            9: op9,
            10: op10,
            11: op11
        }
        self.last_sequence = data['s']
        await handlers.get(data['op'], unknown_op)()

    async def _run(self):
        """
        Run the gateway (called automatically)
        """
        while not self.ws.closed:
            try:
                res = await self.ws.recv()
            except websockets.ConnectionClosed as e:
                # if self.ws.closed: break
                logger.error(f'Gateway closed! Code = {e.code} ({e.reason})')
                await self.disconnect()
                asyncio.ensure_future(self._resume())
                break
            else:
                await self._handle_message(json.loads(res))

    async def _resume(self):
        """
        Attempt to resume the gateway connection after a disconnect
        """
        reconnect_packet = {
            'op': 6,
            'd': {
                'token': self.token,
                'session_id': cache_get('clientinfo')['session_id'],
                'seq': self.last_sequence
            }
        }
        # Close codes said to require another identify
        if self.ws.close_code in (4007, 4009):
            self.identified = False
        # Keep trying to reconnect
        while self.ws.closed:
            logger.debug('Trying to resume gateway...')
            try:
                self.ws = await websockets.connect(self.gateway_url, compression=None)
            except gaierror as e:
                logger.warn(
                    f'Could not reconncet to "{self.gateway_url}"! {e}')
                logger.debug(f'Trying again in {self.sleep_resume}s...')
                await asyncio.sleep(self.sleep_resume)
        # Reconnected!
        logger.debug('Reconnected!')
        await self._send(reconnect_packet)
        asyncio.ensure_future(self._run())
        # Send all queued messages
        while self.send_queue:
            await self._send(self.send_queue.pop(0))

    def _heartbeat(self, heartbeat_stop: threading.Event, onetime=False):
        """
        Heartbeat connection
        """
        # If we haven't received a pong response since the last heartbeat ping, PANIC (I mean reconnect)
        if not self.heartbeat_acked:
            logger.error('No heartbeat ACK received!')
            asyncio.ensure_future(self.disconnect())
            asyncio.ensure_future(self._resume())
            return
        self.heartbeat_acked = False
        # Send Heartbeat
        asyncio.ensure_future(self._send({
            'op': 1,
            'd': self.last_sequence
        }), loop=self.loop)
        if not heartbeat_stop.is_set() and not onetime:
            self.heartbeat_timer = threading.Timer(float(self.heartbeat_ms)/1000.00,
                                                   self._heartbeat, [heartbeat_stop])
            self.heartbeat_timer.start()

    async def _identify(self):
        """
        Send an identify packet to Discord
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
        self.identified = True
