import asyncio

import aiohttp

from modbus_client.communication import serializer
from modbus_client.resources.codes import Codes

conf = {
    'host': 'localhost',
    'port': '3456'
}


class Connection:
    _pending_responses = dict()

    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(
            'ws://' + ':'.join([conf['host'], conf['port']]) + '/ws')
        return (await self.ws.receive()).data

    async def ws_writer(self, message: dict):
        transaction_id = message['transaction_id']
        pending_response = asyncio.Future()
        self._pending_responses[transaction_id] = pending_response
        serialized_message = serializer.serialize_message(message)
        await self.ws.send_bytes(bytes.fromhex(serialized_message))
        response_dict = await pending_response
        response_dict['raw_request'] = bytes.fromhex(serialized_message[16:])
        response_dict['address'] = message['address']
        response_dict['count'] = message.get('count')
        return response_dict

    async def read_writer(self, function_code, transaction_id, unit_address, first_address, count):
        pending_response = asyncio.Future()
        self._pending_responses[transaction_id] = pending_response
        serialized_message = serializer.serialize_read(function_code, transaction_id, unit_address,
                                                       first_address, count)
        await self.ws.send_bytes(bytes.fromhex(serialized_message))
        response_dict = await pending_response
        response_dict['raw_request'] = bytes.fromhex(serialized_message[16:])
        response_dict['address'] = first_address
        response_dict['count'] = count
        return response_dict

    async def read_coils(self, transaction_id, unit_address, first_address, count):
        return await self.read_writer(Codes.READ_COILS.value, transaction_id, unit_address, first_address, count)

    async def read_discrete_inputs(self, transaction_id, unit_address, first_address, count):
        return await self.read_writer(Codes.READ_DISCRETE_INPUTS.value, transaction_id, unit_address, first_address,
                                      count)

    async def read_holding_registers(self, transaction_id, unit_address, first_address, count):
        return await self.read_writer(Codes.READ_HOLDING_REGISTERS.value, transaction_id, unit_address, first_address,
                                      count)

    async def read_input_registers(self, transaction_id, unit_address, first_address, count):
        return await self.read_writer(Codes.READ_INPUT_REGISTERS.value, transaction_id, unit_address, first_address,
                                      count)

    async def write_single_coil(self, transaction_id, unit_address, first_address, status):
        pending_response = asyncio.Future()
        self._pending_responses[transaction_id] = pending_response
        serialized_message = serializer.serialize_write_single_coil(transaction_id, unit_address, first_address, status)
        print(serialized_message)
        await self.ws.send_bytes(bytes.fromhex(serialized_message))
        response_dict = await pending_response
        response_dict['raw_request'] = bytes.fromhex(serialized_message[16:])
        response_dict['address'] = first_address
        return response_dict

    async def write_single_register(self, transaction_id, unit_address, address, data):
        pending_response = asyncio.Future()
        self._pending_responses[transaction_id] = pending_response
        serialized_message = serializer.serialize_write_single_register(transaction_id, unit_address, address, data)
        print(serialized_message)
        await self.ws.send_bytes(bytes.fromhex(serialized_message))
        response_dict = await pending_response
        response_dict['raw_request'] = bytes.fromhex(serialized_message[16:])
        response_dict['address'] = address
        return response_dict

    async def write_multiple_registers(self):
        pass

    async def write_multiple_coils(self):
        pass

    async def ws_reader(self):
        while True:
            message = serializer.deserialize_message((await self.ws.receive()).data)
            if type(message) != str:
                self._pending_responses[message['transaction_id']].set_result(message)
