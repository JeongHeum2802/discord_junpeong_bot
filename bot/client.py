# discor bot의 이벤트 연결

import discord

from bot.history import ChannelHistoryManager
from bot.queue_worker import RequestQueueManager
from bot.commands import remove_bot_mention, handle_command


def create_client() -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    history_manager = ChannelHistoryManager()
    queue_manager = RequestQueueManager(client, history_manager)

    @client.event
    async def on_ready():
        print(f"봇 로그인 완료: {client.user}")
        queue_manager.start_worker()

    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if client.user not in message.mentions:
            return

        user_prompt = remove_bot_mention(message, client.user)

        command_handled = await handle_command(
            message=message,
            user_prompt=user_prompt,
            history_manager=history_manager
        )

        if command_handled:
            return
        else:
            await queue_manager.enqueue(message, user_prompt)

    return client