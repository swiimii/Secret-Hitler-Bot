import discord
import random
import time

class shGame:
    gameServers = [] # list of Game instances
    gameTimeout = 600 # time before a game will be caught by cleanup

    def __init__(self,client,message, gamechannel):
        #server instance variables
        self.inProgress = False
        self.channel = gamechannel
        self.server = message.server

        #game instance variables
        self.players = [] + [message.author]
        self.fascists = []
        self.liberals = []
        self.hitler = "none"
        self.deadPlayers = []
        self.president = "none"
        self.chancellor = "none"
        self.votes = "none"
        self.governmentApproved = False

        self.fascistsPolicies = 0
        self.liberalPolicies = 0
        self.chaosTracker = 0
        self.policyPile = Pile()
        self.discardPile = Pile()
        shGame.gameServers += [self]
        self.events = [("Game Created", time.time())]
        self.client = client

    async def createGame(client,message):

        server = message.author.server
        everyone = discord.PermissionOverwrite(read_messages=False)

        bot = discord.PermissionOverwrite()
        bot.send_message = True
        bot.read_messages = True
        #if there is a finished game or a sh channel from a crashed/closed bot, clean up
        await shGame.shCleanup(client, message)
        channel = await client.create_channel(server, 'secret-hitler-game', (server.default_role, everyone), (server.me, bot))
        thisGame = shGame(client, message, channel)
        await thisGame.announceGame(message)

        #populate policy pile
        for i in range(17): #0-16 - in a game of secret hitler, there are 6 liberal policies, and 11 fascist policies
            if i < 6:
                team = 1 # liberal
            else:
                team = 0 # fascist
            thisGame.policyPile.policies += [Policy(team)]
        thisGame.policyPile.shuffle()



    async def startGame(self):
        self.inProgress = True
        self.events += ("Game Started", time.time())
        #define player roles & notify those players
        await self.assignPlayerRoles()

        #select a president
        self.president = self.players[random.randint(0,len(self.players)-1)]
        await callForAction("Select Chancellor")

    async def callForAction(self, reason):
        #call a vote in self.channel according to reason
        if reason == "Select Chancellor":
            await self.client.send_message("{0.mention}, please select a chancellor.").format(self.president)
        elif reason == "Vote On Government":
            await self.client.send_message("Everyone, please vote on this government. Vote by sending y / n to this bot in a DM.")


    async def receiveVote(message):
        for game in shGame.gameServers:
            if message.author in game.players:
                True
                # receive a vote in dms


    async def assignPlayerRoles(self):
        #assign team ratios
        await self.definePlayerRatios()

        # assign roles

        players = list(self.players) #create separate list of players
        while players != []:
            if True: #len(self.fascists) < self.fascistsNumber:
                self.fascists += [players.pop(random.randint(0,len(players)-1))]
            elif len(self.liberals) < self.liberalsNumber:
                self.liberals += [players.pop(random.randint(0,len(players)-1))]

        # Choose hitler. First player was chosen at random, so this is random
        msg =""
        for p in self.fascists:
            msg += p.name
        await self.client.send_message(self.channel, msg)
        self.hitler = self.fascists[0]
        # self.hitler = self.fascists[random.randint(0,len(players)-1)]


    async def isRecent(self):
        # Return false if game is idle for > 10 minutes
        return time.time() - self.events[-1][1] < shGame.gameTimeout

    async def addPlayer(self, message):
        if message.author not in self.players:
            self.players += [message.author]
            overwrite = discord.PermissionOverwrite()
            overwrite.read_messages = True
            overwrite.send_message = not self.inProgress
            await self.client.edit_channel_permissions(self.channel, message.author, overwrite)
        else:
            await self.client.send_message(message.channel, "You are already in this game!")

    #remove all secret hitler game instances in the server which have non-recent last events
    async def shCleanup(client,message):
        cleaned = False
        game = await shGame.getGame(message)
        if game:
            shGame.gameServers.remove(game)
            cleaned = True
        for c in message.server.channels:
            if c.name == 'secret-hitler-game':
                await client.delete_channel(c)
                # cleaned = True
                break
        if cleaned and message: # if the channel still exists
            await client.send_message(message.channel, "Cleaned up.")
        return True

    async def removePlayer(self, message):
        if message.author in self.players:
            self.players.remove(message.author)
            overwrite = discord.PermissionOverwrite()
            overwrite.read_messages = False
            overwrite.send_message = False
            await self.client.edit_channel_permissions(self.channel, message.author, overwrite)
            msg = "{} has left the game.".format(message.author)
            await self.client.send_message(self.channel, msg)

    async def getGame(message):
        for game in shGame.gameServers:
            if game.server == message.server:
                return game
        return []


    async def definePlayerRatios(self):
        self.fascistsNumber = len(self.players) // 2 - 1
        self.liberalsNumber = len(self.players) - self.fascistsNumber
        # Randomly add a number of players to each team, according to these ratios


    async def announceGame(self,message):
        announcemsg = """A Secret Hitler game is starting! \nType **sh-join** to join in! """
        await self.client.send_message(message.channel,announcemsg)
        newgamemsg = """Welcome to Secret Hitler, \nOnce everybody's in, type \n**sh-begin** to start the game! """
        await self.client.send_message(self.channel,newgamemsg)




    #helper classes

class Policy:
    def __init__(self,team):
        self.team = team # Team is a number - 0 for fascist, 1 for liberal

        def __repr__(self):
            if team == 1:
                return "Liberal"
            elif team == 0:
                return "Fascist"
            else:
                return "Error"

class Pile:
    def __init__(self):
        self.policies = []
    def shuffle(self):
        newPile = []
        for p in self.policies:
            index = random.randint(0, len(self.policies)-1)
            newPile += [self.policies[index]]
        self.policies = newPile
    def combine(self,other):
        self.policies += other.policies
        other.policies = []
        self.shuffle()


class Player:
    def __init__(self, user):
        self.team = "none"
        self.vote = "none"
        self.player = user
    def __repr__(self):
        return self.player
