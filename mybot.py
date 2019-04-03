import discord
from classes import shGame

client = discord.Client()

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Check if the bot is working ---- Switch to "help" function?
    if message.content.startswith('!hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await client.send_message(message.channel, msg)

    # Start a game
    if message.content.startswith('!sh-start'):
        server = message.author.server
        await shStart(message)

    # Clean up empty servers, to allow the start of a new game
    if message.content.startswith('!sh-cleanup'):
        if message.author.server_permissions.administrator:
            await shCleanup(message.author.server)
            for game in shGame.gameServers:
                if game.server == message.server:
                    await client.delete_channel(game.channel)
                    await client.send_message(message.channel, "Cleaned up!")

        # https://stackoverflow.com/questions/48141407/how-would-i-make-my-python-3-6-1-discord-bot-create-a-new-text-channel-in-a-serv

async def shStart(message):
    # start a game of secret hitler, and add it to the gameServers list
    server = message.author.server
    everyone = discord.PermissionOverwrite(read_messages=False)
    player = discord.PermissionOverwrite(read_messages=True)
    for c in server.channels:
        if c.name == 'secret-hitler-game':
            await client.delete_channel(c)
            break
    channel = await client.create_channel(server, 'secret-hitler-game', (server.default_role, everyone), (server.me, player))
    thisGame = shGame(client, message, channel)
    shGame.gameServers += [thisGame]
    await thisGame.announceGame(message)

async def shCleanup(server):
    check = True
    #remove all secret hitler game instances in the server which have non-recent last events

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run('NTYyNDAwODUyMzY3OTAwNjg0.XKKPVA.DVtDmn-n_kzNcEEO9BeMKJX_WtA')  # 'Token'
