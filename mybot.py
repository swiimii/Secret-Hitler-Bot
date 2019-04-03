import discord
from classes import secretHitlerGame


client = discord.Client()

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

    if message.content.startswith('!shb-start'):

        server = message.author.server
        everyone = discord.PermissionOverwrite(read_messages=False)
        player = discord.PermissionOverwrite(read_messages=True)
        await client.create_channel(server, 'secret-hitler-game', (server.default_role, everyone), (message.author, player))
        channel = c.name == server.channels
        secretHitlerGame(client, message.author, message.channel, server)
        # https://stackoverflow.com/questions/48141407/how-would-i-make-my-python-3-6-1-discord-bot-create-a-new-text-channel-in-a-serv



@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')



client.run('NTYyNDAwODUyMzY3OTAwNjg0.XKKPVA.DVtDmn-n_kzNcEEO9BeMKJX_WtA')  # 'Token'
