from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'orders'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'order_update',
                'message': message
            }
        )

    async def order_update(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))