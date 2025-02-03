import discord
import dotenv
import os
import ast
from openai import OpenAI
import asyncio
from random import randint

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) 
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) 

class BotBrain(discord.Client):
    def __init__(self, filename, prompt, typing_speed=70):
        super().__init__()
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
                self.interaction_id += 1
                current_id = self.interaction_id
                self.user_message(str(message.author), str(message.content))
                await asyncio.sleep(randint(600, 5000)/1000)
                if self.interaction_id == current_id:
                    response = self.generate_response(starting_prompt)
                    typing_speed = BotBrain.calculate_typing_duration(self.typing_speed, response)
                    response_time = len(response) / typing_speed
                    await self.display_typing(message.channel, response_time)
                    if self.interaction_id == current_id:
                        self.bot_message(response)
                        await message.channel.send(response)
            return
        
    # Discord Functionality
    async def display_typing(self, channel, length):
        async with channel.typing():
            await asyncio.sleep(length)

    def calculate_typing_duration(self, message):
        typing_speed = 5 * self.typing_speed / 60
        response_time = len(message) / typing_speed
        return response_time

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
client = BotBrain("message_history.txt", starting_prompt)
client.run(TOKEN)