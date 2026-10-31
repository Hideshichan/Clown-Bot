# This example requires the 'message_content' intent.

import discord
import math
import random

x = random.randint(0, 100)
on = True
creator = 1267529062713266380, 689517066864427075

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    #autism radar
    if message.content==('echo autism'):
        await message.channel.send(f"You are {x}% autistic!")
        print(f'someone has used the !autism command')
    #admin permission check
    if message.content==("sudo"):
        if (message.author.id == 1267529062713266380, 689517066864427075):
            await message.channel.send("you have admin permisions!")
            print(f"the idiot checked if he had perms")
        elif (message.author.id != 1267529062713266380 or 689517066864427075):
            await message.channel.send("you dont have admin capabilities :/")
    #exit command
    if message.content==("sudo exit"):
        if (message.author.id == 1267529062713266380, 689517066864427075):
            await message.channel.send(f"The script running the bot will now exit!\n @spaveywavey the bot is off.")
            exit()
        if (message.author.id != 1267529062713266380, 689517066864427075):
            await message.channel.send("Nice try hahahahahahahahahaahah")
    else:
        if on == (False):
            #something here
            message.channel.send("this is just a placeholder")

client.run('bot key goes here')
