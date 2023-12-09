import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
logger = logging.getLogger(__name__)
# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = "chat_%s" % self.room_name

#         # Join room group
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)

#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     # Receive message from WebSocket
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json["message"]

#         # Send message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name, {"type": "chat_message", "message": message}
#         )

#     # Receive message from room group
#     async def chat_message(self, event):
#         message = event["message"]

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({"message": message}))
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id = self.scope['user'].id
        await self.channel_layer.group_add(
            user_id,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # You can handle received messages if needed
        user_id = self.scope['user'].id
        await self.channel_layer.send(user_id,
                {'message': "haha",
                'to_user': user_id,})
        pass

    async def send_notification(self, event):
        try:
            message = event.get('message', None)
            if message is not None:
                await self.send(text_data=json.dumps({
                    'message': message
                }))
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
class LikeNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket HANDSHAKING")
        await self.accept()
        logger.info("WebSocket CONNECT")

    async def disconnect(self, close_code):
        logger.info("WebSocket DISCONNECT")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        logger.info(f"WebSocket MESSAGE: {message}")

        # Xử lý thông điệp và gửi phản hồi

        # Ví dụ:
        await self.send(text_data=json.dumps({
            'message': 'Received your message: ' + message
        }))
