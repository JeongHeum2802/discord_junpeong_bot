# 문맥 reset time 관리 클래스
# get_recent_messages로 reset time 이후의 history 파싱 가능

import discord
from config import HISTORY_SCAN_LIMIT


class ChannelHistoryManager:
    def __init__(self):
        self.channel_reset_times = {}

    def reset_channel(self, message: discord.Message):
        self.channel_reset_times[message.channel.id] = message.created_at

    async def get_recent_messages(
        self,
        message: discord.Message,
        client_user: discord.ClientUser,
        limit: int = 10
    ) -> list[dict]:
        recent_messages = []

        reset_time = self.channel_reset_times.get(message.channel.id)

        async for msg in message.channel.history(limit=HISTORY_SCAN_LIMIT):
            if msg.id == message.id:
                continue

            if reset_time is not None and msg.created_at <= reset_time:
                continue

            if not msg.content.strip():
                continue

            role = "assistant" if msg.author == client_user else "user"
            content = f"{msg.author.display_name}: {msg.content}"

            recent_messages.append({
                "role": role,
                "content": content
            })

            if len(recent_messages) >= limit:
                break

        recent_messages.reverse()
        return recent_messages