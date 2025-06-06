import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # הצטרפות לקבוצת החדר
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # עזיבת קבוצת החדר
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        # שליחת התשובה בחזרה למשתמש (בגרסה פשוטה לפני חיבור ל-AI)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f"קיבלתי את ההודעה שלך: {message}",
                'sender': 'bot'
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # שליחת ההודעה לחיבור WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))