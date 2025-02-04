import discord
import dotenv
import os
import ast
from openai import OpenAI
import asyncio
from random import randint
import time

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) 
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WELCOME_BOT = int(os.getenv("WELCOME_BOT_ID"))

class BotBrain(discord.Client):
    def __init__(self, filename, prompt, typing_speed=70, focus_length = 30, refocus_time = 10, thinking_time=500, responds_to=set(), welcome_bot=0):
        super().__init__()
        self.responds_to = responds_to

        self.welcome_bot = welcome_bot

        self.last_channel = 0
        self.last_message_time = 0

        self.focus_length = focus_length
        self.refocus_time = refocus_time

        self.thinking_time = thinking_time

        self.typing_speed = typing_speed

        self.interaction_id = 0
        self.filename = filename
        self.message_history = []
        self.prompt = prompt
        self.server = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
        self.load_messages()

    # Discord.py Events
    async def on_ready(self):
        self.prompt = self.prompt.replace("[username]", str(self.user)[:-2])
        print('Logged on as', self.user)

    async def on_message(self, message):
        if message.author != self.user:
            if message.guild.id == GUILD_ID and message.channel.id == CHANNEL_ID:
                if message.author.id == self.welcome_bot:
                    welcomed = BotBrain.get_welcomed_user(message)
                    self.add_to_respond_to(welcomed)
                if message.author.id in self.responds_to:
                    message = BotBrain.parse_message(message)
                    if len(message.content) > 0:
                        self.interaction_id += 1
                        current_id = self.interaction_id
                        self.user_message(str(message.author), str(message.content))
                        await asyncio.sleep(self.calculate_response_wait(message.channel))
                        if self.interaction_id == current_id:
                            self.focus_channel(message.channel)
                            response = self.generate_response(starting_prompt)
                            response_time = self.calculate_typing_duration(response)
                            await self.display_typing(message.channel, response_time)
                            if self.interaction_id == current_id:
                                self.bot_message(response)
                                await message.channel.send(response)
                                self.focus_channel(message.channel)
                if message.author.id == self.welcome_bot:
                    await asyncio.sleep(120)
                    self.remove_from_respond_to(welcomed)
            return
        
    # Discord Functionality
    async def display_typing(self, channel, length):
        async with channel.typing():
            await asyncio.sleep(length)

    def calculate_response_wait(self, channel):
        time_since_last_message = time.time() - self.last_message_time
        if time_since_last_message > self.focus_length or channel.id != self.last_channel:
            return self.refocus_time
        return self.thinking_time / 1000

    def focus_channel(self, channel):
        self.last_channel = channel.id
        self.last_message_time = time.time()

    def calculate_typing_duration(self, message):
        typing_speed = 5 * self.typing_speed / 60
        response_time = len(message) / typing_speed
        return response_time

    def add_to_respond_to(self, member_id):
        self.responds_to.add(member_id)

    def remove_from_respond_to(self, member_id):
        self.remove(member_id)

    @classmethod
    def get_welcomed_user(self, message):
        return message.raw_mentions[0]

    @classmethod
    def parse_message(cls, message):
        message.content = message.content.encode('utf-8').decode('ascii', 'ignore')
        id_to_name = {}
        for member in message.mentions:
            id_to_name[member.id] = member.name
        for member_id in id_to_name:
            message.content = message.content.replace(str(member_id), id_to_name[member_id])
        return message

    # AI Functionality
    def load_messages(self):
        with open(self.filename) as file:
            messages = file.readlines()
            for message in messages:
                self.message_history.append(ast.literal_eval(message))

    def generate_response(self, prompt):
        formatted_prompt = {"role": "system", "content": prompt}
        temp_cache = [formatted_prompt] + self.message_history
        completion = self.server.chat.completions.create(
            model="local-model",
            messages=temp_cache,
            temperature=0,
        )
        return completion.choices[0].message.content

    def bot_message(self, message):
        formatted_message = {"role": "assistant", "content": message}
        self.message_history.append(formatted_message)
        self.save_message(formatted_message)

    def user_message(self, author, message):
        message = f"received message '{message}' from '{author}'"
        formatted_message = {"role": "user", "content":message}
        self.message_history.append(formatted_message)
        self.save_message(formatted_message)

    def save_message(self, formatted_message):
        f = open(self.filename, "a")
        f.write(f"{str(formatted_message)}\n")
        f.close()

    def get_message_history(self):
        return self.message_history



starting_prompt = ""
with open("starting_prompt.txt") as prompt:
    starting_prompt = prompt.read()
client = BotBrain("message_history.txt", starting_prompt, welcome_bot=WELCOME_BOT)
client.run(TOKEN)