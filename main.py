import discord
import dotenv
import os
import ast


dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) 



starting_prompt = ""
with open("starting_prompt.txt") as prompt:
    starting_prompt = prompt.read()


class BotBrain():
    def __init__(self, filename):
        self.filename = filename
        self.message_history = []
        with open(filename) as file:
            messages = file.readlines()
            for message in messages:
                self.message_history.append(ast.literal_eval(message))

    def bot_message(self, message):
        formatted_message = {"role": "assistant", "content": message}
        self.message_history.append(formatted_message)
        self.save_message(formatted_message)

    def user_message(self, author, message):
        message = f"{author}: {message}"
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

message_cache = [{"role": "system", "content": starting_prompt}]

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # only respond to ourselves
        if message.author != self.user:
            if message.guild.id == GUILD_ID:
                bot_brain.user_message(str(message.author), str(message.content))
                print(message.content)
            return

client = MyClient()
client.run(TOKEN)