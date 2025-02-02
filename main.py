import discord
import dotenv
import os
import ast
from openai import OpenAI

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) 
CHANNEL_ID = int(os.getenv("GUILD_ID")) 


starting_prompt = ""
with open("starting_prompt.txt") as prompt:
    starting_prompt = prompt.read()

class BotBrain():
    def __init__(self, filename):
        self.filename = filename
        self.message_history = []
        self.server = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
        with open(filename) as file:
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
        print(self.message_history)
        f.write(f"{str(formatted_message)}\n")
        f.close()

    def get_message_history(self):
        return self.message_history
    
bot_brain = BotBrain("message_history.txt")
print(bot_brain.get_message_history())

class MyClient(discord.Client):
    def __init__(self):
        interaction_id = 0

    async def on_ready(self):
        global starting_prompt
        starting_prompt = starting_prompt.replace("[username]", str(self.user)[:-2])
        print('Logged on as', self.user)

    async def on_message(self, message):
        # only respond to ourselves
        if message.author != self.user:
            if message.guild.id == GUILD_ID and message.channel.id == CHANNEL_ID:
                bot_brain.user_message(str(message.author), str(message.content))
                response = bot_brain.generate_response(starting_prompt)
                bot_brain.bot_message(response)
                await message.channel.send(response)
            return

client = MyClient()
client.run(TOKEN)