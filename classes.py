import discord
import random
import time

class shGame:
    gameServers = [] # list of Game instances
    gameTimeout = 600 # time before a game will be caught by cleanup -- 10 minutes

    def __init__(self,client,message, gamechannel):
        #server instance variables
        self.inProgress = False
        self.channel = gamechannel
        self.server = message.server

        #game instance variables
        self.players = Pile([Player(message.author, self)])
        self.fascists = []
        self.liberals = []
        self.hitler = "none"
        self.deadPlayers = []
        self.president = "none"
        self.chancellor = "none"
        self.previousGovernment = []
        self.votes = "none"
        self.governmentApproved = False
        self.awaitingAction = "Begin Game"

        self.fascistsPolicies = 0
        self.maxFascists = 6
        self.liberalPolicies = 0
        self.maxLiberals = 5
        self.chaosTracker = 0
        self.policyPile = Pile()
        self.discardPile = Pile()
        shGame.gameServers += [self]
        self.events = [("Game Created", time.time())]
        self.client = client

    async def createGame(client,message):

        #if there is a finished game or a sh channel from a crashed/closed bot, clean up
        await shGame.shCleanup(client, message)

        server = message.author.server
        everyone = discord.PermissionOverwrite(read_messages=False)

        bot = discord.PermissionOverwrite()
        bot.send_message = True
        bot.read_messages = True

        channel = await client.create_channel(server, 'secret-hitler-game', (server.default_role, everyone), (server.me, bot))
        thisGame = shGame(client, message, channel)

        #populate policy pile
        for i in range(17): #0-16 - in a game of secret hitler, there are 6 liberal policies, and 11 fascist policies
            if i < 6:
                team = "Liberal" # liberal
            else:
                team = "Fascist" # fascist
            thisGame.policyPile.content += [Policy(team)]
        thisGame.policyPile.shuffle()
        await thisGame.announceGame(message)


    async def startGame(self):
        self.inProgress = True
        self.events += ("Game Started", time.time())
        #define player roles & notify those players
        await self.assignPlayerRoles()

        self.players.shuffle() # Prevent teams from being predictable
        self.president = self.players.content[0] #select a president
        await self.callForAction("Select Chancellor")

    async def callForAction(self, reason):
        #call a vote in self.channel according to reason
        self.awaitingAction = reason

        if reason == "Select Chancellor":
            await self.client.send_message(self.channel, "{0.mention}, please select a chancellor. Copy the ID of the player you want to select, then type 'select #################' in my DMs".format(self.president.user))
        elif reason == "Vote On Government":
            await self.client.send_message(self.channel, "{0} has selected {1} as their chancellor.".format(self.president.user.mention, self.chancellor.user.mention))
            await self.client.send_message(self.channel, "Vote yes or no to this government, by DMing me **vote yes** or **vote no**.")
        elif reason == "President Discard":
            await self.client.send_message(self.channel, "{0.mention}, please discard a policy. I've sent you a DM.".format(self.president.user))
        elif reason == "Chancellor Discard":
            await self.client.send_message(self.channel, "{0.mention}, please discard one of the cards given to you by the President.".format(self.chancellor.user))

    # Private Message received by the bot
    async def resolvePlayerInput(self, message, player):
        if message.content.startswith("vote"):
            if "Vote" in self.awaitingAction:
                if "y" in message.content or "Y" in message.content:
                    player.vote = 'y'
                    await self.client.send_message(message.channel, "Yes Vote received")
                    await self.checkVotes()
                elif "n" in message.content or "N" in message.content:
                    player.vote = 'n'
                    await self.client.send_message(message.channel, "No Vote received")
                    await self.checkVotes()

        elif message.content.startswith("select"):
            if "Select Chancellor" in self.awaitingAction and message.author == self.president.user:
                #set player with ID to chancellor, move to next phase
                idInput = message.content.split(' ')[1]
                found = False
                for p in self.players.content:
                    if p.user.id == idInput:
                        found = True
                        self.chancellor = p
                        await self.callForAction("Vote On Government")

                if not found:
                    await self.client.send_message(message.channel, "Copy a user's ID, then type 'select ######' here.")
            elif "Select Ability" in self.awaitingAction and message.author == self.president.user:
                True #resolve ability, and do what's necessary to proceed
            else: #Not waiting on this player to select
                await self.client.send_message(message.channel, "There is nothing to select for you right now.")

        # Awaiting president or chancellor discard
        elif message.content.startswith("discard"):
            if "President Discard" in self.awaitingAction and message.author == self.president.user:
                input = message.content.split(' ')[1]
                success = False

                if str(input) == '1':
                    self.discardPile.content += [self.policyPile.content.pop(0)]
                    success = True
                elif str(input) == '2':
                    self.discardPile.content += [self.policyPile.content.pop(1)]
                    success = True
                elif str(input) == '3':
                    self.discardPile.content += [self.policyPile.content.pop(2)]
                    success = True
                else:
                    await self.client.send_message(message.channel, "Type 'discard #', with a number between 1 and 3, to discard a policy")

                if success:
                    await self.client.send_message(message.channel, "Discard successful")
                    await self.client.send_message(self.channel, "The president has discarded a policy. {0}, please discard a policy.".format(self.chancellor.user.mention))
                    await self.callForAction("Chancellor Discard")
                    await self.revealPolicies("Chancellor")

            elif "Chancellor Discard" in self.awaitingAction and message.author == self.chancellor.user:
                input = message.content.split(' ')[1]
                success = False

                if str(input) == '1':
                    self.discardPile.content += [self.policyPile.content.pop(0)]
                    success = True
                elif str(input) == '2':
                    self.discardPile.content += [self.policyPile.content.pop(1)]
                    success = True


                if success:
                    await self.client.send_message(message.channel, "Discard successful")
                    await self.client.send_message(self.channel, "{0} has discarded a policy. A {1} policy has been added to the board.".format(self.chancellor.user.mention, self.policyPile.content[0].team))
                    if self.policyPile.content[0].team == "Fascist":
                        power = True
                        self.fascistsPolicies += 1
                    elif self.policyPile.content[0].team == "Liberal":
                        power = False
                        self.liberalPolicies += 1
                    if power:
                        True #do power according to number of fascist policies played
                    self.policyPile.content.pop(0) # This policy is now considered part of the board
                    await self.resetGovernment(success)
                    await self.displayTracks()
                    #check if game is over
                    progressMessage = await self.checkGameOver()
                    if "Win" in progressMessage:
                        await self.client.send_message(self.channel, progressMessage + " Start a new game by typing **sh-start**.")
                        return True

                    msg = "There are {0} cards left in the draw pile. ".format(len(self.policyPile.content))
                    if len(self.policyPile.content) < 3:
                        self.policyPile.combine(self.discardPile)
                        msg += "Therefore the pile will be shuffled now."
                    await self.client.send_message(self.channel, msg)
                    await self.callForAction("Select Chancellor")

    async def resetGovernment(self, success):
        if success:
            self.previousGovernment = [self.president, self.chancellor]
        self.president = self.players.content[(self.players.content.index(self.president) + 1) % len(self.players.content)]
        self.chancellor = 'none'


    async def displayTracks(self):
        msg = "There are now {0}/{1} liberal policies, and {2}/{3} fascist policies.".format(self.liberalPolicies, self.maxLiberals, self.fascistsPolicies, self.maxFascists)
        await self.client.send_message(self.channel, msg)

    async def checkGameOver(self):
        if self.hitler in self.deadPlayers:
            self.inProgress = False
            self.awaitingAction = "None"
            return "**Liberals Win!**"
        elif self.liberalPolicies >= self.maxLiberals:
            self.inProgress = False
            self.awaitingAction = "None"
            return "**Liberals Win!**"
        elif self.fascistsPolicies >= self.maxFascists:
            self.inProgress = False
            self.awaitingAction = "None"
            return "**Fascists Win!**"
        else:
            return "Resume"


    async def checkVotes(self):
        for player in self.players.content:
            if player.vote == 'none':
                return False
        await self.resolveVotes()

    async def resolveVotes(self):

        yes = 0
        no = 0
        for player in self.players.content:
            if player.vote == 'y':
                yes += 1
            elif player.vote == 'n':
                no += 1
        success = yes > no
        await self.revealVotes()
        await self.resetVotes()
        #Players only vote on governments
        if success:
            #Move to discard phase
            #check if decks need to be combined

            self.awaitingAction = "President Discard"
            await self.revealPolicies("President")
        else:
            await self.failGovernment()

    async def revealVotes(self):
        msg = "The votes are in! These are the results:\n"
        for player in self.players.content:
            msg += "\t" + player.user.mention + ", " + player.vote + "\n"
        await self.client.send_message(self.channel, msg)


    async def revealPolicies(self, target):
        if target == "President":
            msg = "The top three policies are 1: " + self.policyPile.content[0] + ", 2: " + self.policyPile.content[1]  + ", 3: " + self.policyPile.content[2] + ".\n"
            msg += "Tell me 'discard #' and a number between 1 and 3, to **discard** that policy. The remaining policies will be send to the chancellor."
            await self.client.send_message(self.president.user, msg)
        elif target == "Chancellor":
            msg = "The policies given to you by the president are 1: " + self.policyPile.content[0] + ", 2: " + self.policyPile.content[1]  + ".\n"
            msg += "Tell me 'discard #' and a number between 1 and 2, to discard that policy. The remaining policy will be locked in, and revealed."
            await self.client.send_message(self.chancellor.user, msg)

        elif target == "Everyone":
            True

    async def failGovernment(self, type = 'default'):
        nextPresIndex = self.players.content.index(self.president) + 1 % len(self.players.content)
        self.president = self.players.content[nextPresIndex]
        chancellor = 'none'
        await self.client.send_message(self.channel, "The government vote has failed.")
        self.awaitingAction = "Select Chancellor"

    async def resetVotes(self):
        for player in self.players.content:
            player.vote = 'none'




    async def assignPlayerRoles(self):
        #assign team ratios
        await self.definePlayerRatios()

        # assign roles

        players = list(self.players.content) #create separate list of players
        while players != []:
            index = random.randint(0,len(players)-1)
            if True: #len(self.fascists) < self.fascistsNumber:
                players[index].team = "Fascist"
                await self.client.send_message(players[index].user, "You are a Fascist")
                self.fascists += [players.pop(index)]

            elif len(self.liberals) < self.liberalsNumber:
                players[index].team = "Liberal"
                await self.client.send_message(players[index].user, "You are a Liberal")
                self.liberals += [players.pop(index)]

        # Choose hitler. First player was chosen at random, so this is random
        msg =""
        for p in self.fascists:
            msg += p.user.name
        await self.client.send_message(self.channel, msg)
        self.hitler = self.fascists[0]
        # self.hitler = self.fascists[random.randint(0,len(players)-1)]



    async def isRecent(self):
        # Return false if game is idle for > 10 minutes
        return time.time() - self.events[-1][1] < shGame.gameTimeout

    async def addPlayer(self, message):
        if message.author not in [player.user for player in self.players.content]:
            self.players.content += [Player(message.author, self)]
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
        if message.author in [player.user for player in self.players.content]:
            self.players.content.remove([player.user for player in self.players.content if player.user == message.author][0])
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
        self.fascistsNumber = len(self.players.content) // 2 - 1
        self.liberalsNumber = len(self.players.content) - self.fascistsNumber
        # Randomly add a number of players to each team, according to these ratios


    async def announceGame(self,message):
        newgamemsg = """Welcome to Secret Hitler, \nOnce everybody's in, type \n**sh-begin** to start the game! """
        await self.client.send_message(self.channel,newgamemsg)

        announcemsg = """A Secret Hitler game is starting! \nType **sh-join** to join in! """
        await self.client.send_message(message.channel,announcemsg)





    #helper classes

class Policy:
    def __init__(self,team):
        self.team = team # Team is a number - 0 for fascist, 1 for liberal

    def __str__(self):
        return self.team
    def __add__(self, other):
        return str(self) + other
    def __radd__(self, other):
        return other + str(self)

class Pile:
    def __init__(self, contents = []):
        self.content = [] + contents


    def shuffle(self):
        newPile = []
        for p in self.content:
            index = random.randint(0, len(self.content)-1)
            newPile += [self.content[index]]
        self.content = newPile
    def combine(self,other):
        self.content += other.content
        other.content = []
        self.shuffle()


class Player:
    def __init__(self, user, gameserver):
        self.team = "none"
        self.vote = "none"
        self.user = user
        self.game = gameserver
    def __repr__(self):
        return self.user
