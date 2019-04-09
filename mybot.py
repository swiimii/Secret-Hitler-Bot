import discord
from classes import shGame

client = discord.Client()

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Check if the bot is working ---- Switch to "help" function?
    if message.content.startswith('sh-help'):
        msg = '''Welcome to Secret Hitler!\nCommands:
    **sh-start**: Start a game
    **sh-cleanup**: end current game (admin)
    **sh-players**: display who's in a game right now
    **sh-join**: join a lobby or spectate a game in progress
    **sh-leave**: leave a game in progress
    **sh-begin**: begin a game from the game lobby
Notes:

    * There is a 5 minute game timeout - if 5 minutes pass between game actions, a new game can be started!

    * 5 players minimum per game

    * One game per server! '''
        await client.send_message(message.channel, msg)

    # Start a game
    if message.content.startswith('sh-start'):
        await shStart(message)

    if message.content.startswith('sh-begin'):
        game = await shGame.getGame(message)
        if game and message.channel == game.channel:
            if len(game.players) > 4:
                await game.startGame()
            else:
                await client.send_message(message.channel, "5 player minimum for a game")

    # Clean up empty servers, to allow the start of a new game
    if message.content.startswith('sh-cleanup'):
        if message.author.server_permissions.administrator:
            await shGame.shCleanup(client,message)
        else: # User is not an admin
            await client.send_message(message.channel, "You need admin permissions to do this.")

    if message.content.startswith('sh-players'):
        game = await shGame.getGame(message)
        if game:
            await displayPlayers(message)

    if message.content.startswith('sh-join'):
        game = await shGame.getGame(message)
        if game:
            await game.addPlayer(message)

    if message.content.startswith('sh-leave'):
        game = await shGame.getGame(message)
        if game:
            await game.removePlayer(message)


async def shStart(message):
    # Check if game will start
    gameWillStart = True
    game = await shGame.getGame(message)
    if game and await game.isRecent():
        gameWillStart = False

    if gameWillStart: # Start game
        await shGame.createGame(client,message)

    else: # Game in progress was found on this server
        await client.send_message(message.channel, "There is a game in progress in this server. \nType **sh-join** to spectate! \nType **sh-help** for more options!")


async def displayPlayers(message):
    game = await shGame.getGame(message)
    if game:
        if game.players is not []:
            msg = 'The players are'
            for player in game.players:
                msg += ", " + player.name
            msg += '.'
            await client.send_message(message.channel, msg)
        else:
            await client.send_message(message.channel, "No players found.")
    else:
        await client.send_message(message.channel, "No game was found on this server.")

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run('NTYyNDAwODUyMzY3OTAwNjg0.XKKPVA.DVtDmn-n_kzNcEEO9BeMKJX_WtA')  # 'Token'
