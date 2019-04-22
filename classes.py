import discord
import random
import time

class shGame:
    gameServers = [] # list of Game instances
    gameTimeout = 420 # time before a game will be caught by cleanup -- 6 minutes

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
        self.previousGovernment = ['none', 'none']
        self.votes = "none"
        self.governmentApproved = False
        self.awaitingAction = "Begin Game" #Very important - This variable allows the code below to know what aspect of the game is currently taking place

        # Dictionary of abilities, independent of number of players
        self.ablilitiesDict = {'Nothing':self.nothing, 'Investigate':self.investigate, 'SpecialElection':self.specialElection, 'SpecialExecution':self.specialExecution, 'PolicyPeek':self.policyPeek, 'Execute':self.execute}
        self.abilitiesList = [] # Names of functions for the sake of calling for their action

        self.fascistPolicies = 0
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

        botAndPlayer = discord.PermissionOverwrite()
        botAndPlayer.send_message = True
        botAndPlayer.read_messages = True

        channel = await client.create_channel(server, 'secret-hitler-game', (server.default_role, everyone), (server.me, botAndPlayer))
        await client.edit_channel_permissions(channel, message.author, botAndPlayer)

        thisGame = shGame(client, message, channel)

        #populate policy pile
        for i in range(17): #0-16 - in a game of secret hitler, there are 6 liberal policies, and 11 fascist policies
            if i < 6:
                team = "Liberal" # liberal
            else:
                team = "Fascist" # fascist
            thisGame.policyPile.content += [Policy(team)]
        thisGame.policyPile.shuffle()

        #announce game in the channel where a player started the game. If the channel was deleted (via shCleanup), an exception will be raised, but the game will still be playable.
        await thisGame.announceGame(message)

    async def addEvent(self, event):
        self.events += [(event, time.time())]

    # called when players are prepared to start the game.
    async def startGame(self):
        self.inProgress = True
        await self.addEvent("Game Started")
        #define player roles & notify those players
        await self.assignPlayerRoles()

        await self.setAbilities()

        self.players.shuffle() # Prevent teams from being predictable

        await self.displayPowers()

        await self.displayTracks()


        self.president = self.players.content[0] #select a president
        await self.callForAction("Select Chancellor")



    async def callForAction(self, reason):
        #call a vote in self.channel according to reason
        self.awaitingAction = reason

        # Actions taken during elections and special elections
        if "Select Chancellor" in reason:
            await self.client.send_message(self.channel, "--------------------\n{0.mention}, please select a chancellor. Copy the ID or Nickname of the player you want to select, then type **select name** in my DMs".format(self.president.user))
        elif "Vote On Government" in reason:
            await self.client.send_message(self.channel, "--------------------\n{0} has selected {1} as their chancellor.".format(self.president.user.mention, self.chancellor.user.mention))
            await self.client.send_message(self.channel, "Vote yes or no to this government, by DMing me **vote yes** or **vote no**.")
        elif "President Discard" in reason :
            await self.client.send_message(self.channel, "--------------------\n{0.mention}, please discard a policy. I've sent you a DM.".format(self.president.user))
        elif "Chancellor Discard" in reason :
            await self.client.send_message(self.channel, "--------------------\n{0.mention}, please discard one of the cards given to you by the President.".format(self.chancellor.user))

        # Ability action calls
        elif reason == "Ability:Nothing":
            await self.client.send_message(self.channel, "--------------------\nThere are no presidential abilities this round")
            await self.resetGovernment(True)
            await self.callForAction("Select Chancellor")

        elif reason == "Ability:PolicyPeek":
            await self.client.send_message(self.channel, "--------------------\n{0.mention} has been DM'd a list of the top three cards in the policy pile. ".format(self.president.user))
            # Policy peek requires no action, however other abilities do. This allows for abilities to be used as a list
            await self.policyPeek(False)

        elif reason == "Ability:Investigate":
            await self.client.send_message(self.channel, "--------------------\n{0.mention}, you now have an ability. Select a player to investigate by DMing me their ID or Nickname using **select username**. You will receive a message telling you what team they're on.".format(self.president.user))

        elif reason == "Ability:SpecialElection":
            await self.client.send_message(self.channel, "--------------------\n{0.mention}, you now have an ability. Elect a player to be president in a Special Election using **select username**. DM me their ID or Nickname using **select username**".format(self.president.user))

        elif reason == "Ability:SpecialExecution":
            await self.client.send_message(self.channel, "--------------------\n{0.mention}, you now have an ability. Select a player to kill by DMing me their ID or Nickname using **select username**. If hitler dies, the Liberals win.".format(self.president.user))

        elif reason == "Ability:Execute":
            await self.client.send_message(self.channel, "--------------------\n{0.mention}, you now have an ability. Select a player to kill by DMing me their ID or Nickname using **select username**. If hitler dies, the Liberals win.".format(self.president.user))

        elif reason == "Veto":
            await self.client.send_message(self.channel, "--------------------\n{0.mention} has asked for a veto. You can allow a veto by DMing me **yes**, or deny the veto by DMing me **no**. If the veto is denied, the chancellor will be forced to play option 1.".format(self.president.user))


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
                else:
                    await self.client.send_message(message.channel, "Vote on this government by typing **vote yes** or **vote no**.")



        elif message.content.startswith("select"):

            # There is a presidential ability in play
            if "Ability:" in self.awaitingAction:
                if message.author == self.president.user:
                    splitIndex = message.content.index(' ')
                    idInput = message.content[splitIndex+1:]
                    found = False
                    for p in self.players.content:
                        if p.user.id == idInput or p.user.name == idInput:
                            abilityName = self.awaitingAction.split(' ')[1]
                            await self.addEvent("Ability:" + abilityName)
                            found = True
                            ability = self.ablilitiesDict[abilityName]
                            await ability(p) # President selected player p for their fascist ability

                    if not found:
                        await self.client.send_message(message.channel, "Copy a user's ID or Nickname, then type **select username** here.")

                else: #Not waiting on this player to select
                    await self.client.send_message(message.channel, "There is nothing to select for you right now, you aren't the president.")

            elif "Select Chancellor" in self.awaitingAction and message.author == self.president.user:
                #set player with ID or Nickname to chancellor, move to next phase
                splitIndex = message.content.index(' ')
                idInput = message.content[splitIndex+1:]
                found = False
                for p in self.players.content:
                    if p.user.id == idInput or p.user.name == idInput:
                        await self.addEvent("Chancellor Selected")
                        found = True
                        self.chancellor = p
                        action = "Vote On Government"
                        if "Special" in self.awaitingAction:
                            action = "Special: " + action
                        await self.callForAction(action)

                if not found:
                    await self.client.send_message(message.channel, "Copy a user's ID or nickname, then type **select user#123** here.")
            else: #Not waiting on this player to select
                await self.client.send_message(message.channel, "There is nothing to select for you right now.")

        # Awaiting president or chancellor discard
        elif message.content.startswith("discard"):
            if "President Discard" in self.awaitingAction and message.author == self.president.user:
                splitIndex = message.content.index(' ')
                input = message.content[splitIndex+1:]
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
                    await self.addEvent("President Discard")
                    await self.client.send_message(message.channel, "Discard successful")
                    await self.client.send_message(self.channel, "The president has discarded a policy.")

                    action = "Chancellor Discard"
                    if "Special" in self.awaitingAction:
                        action = "Special: " + action
                    await self.callForAction(action)
                    await self.revealPolicies("Chancellor")

            elif "Chancellor Discard" in self.awaitingAction and message.author == self.chancellor.user:
                splitIndex = message.content.index(' ')
                input = message.content[splitIndex+1:]
                success = False

                if str(input) == '1':
                    self.discardPile.content += [self.policyPile.content.pop(0)]
                    success = True
                elif str(input) == '2':
                    self.discardPile.content += [self.policyPile.content.pop(1)]
                    success = True
                elif str(input).toLower() == 'veto' and self.fascistPolicies - self.maxFascists == 1:
                    self.callForAction("Veto")



                if success:
                    await self.addEvent("Chancellor Discard")
                    await self.client.send_message(message.channel, "Discard successful")
                    await self.client.send_message(self.channel, "{0} has discarded a policy. A {1} policy has been added to the board.".format(self.chancellor.user.mention, self.policyPile.content[0].team))

                    if self.policyPile.content[0].team == "Fascist":
                        self.fascistPolicies += 1
                    elif self.policyPile.content[0].team == "Liberal":
                        self.liberalPolicies += 1

                    successfulTeam = self.policyPile.content.pop(0).team # This policy is now considered part of the board

                    #check if game is over
                    await self.displayTracks()
                    await self.checkGameOver()
                    if self.awaitingAction == "none":
                        await self.client.send_message(self.channel, progressMessage + " Start a new game by typing **sh-start**.")
                        return True #at this point, the game ends

                    #shuffle pile if necessary
                    if len(self.policyPile.content) < 3:
                        self.policyPile.combine(self.discardPile)
                        msg = "The discard pile will now be shuffled into the draw pile."
                        await self.client.send_message(self.channel, msg)

                    #activate abilities, if a fascist policy was passed
                    if "Special" in self.awaitingAction:
                        if successfulTeam == "Fascist":
                            await self.callForAction("Ability:SpecialExecution")
                        else: # successful team is Liberal - no ability activation
                            await self.resetGovernment(success)
                            await self.callForAction("Select Chancellor")
                    else:
                        if successfulTeam == "Fascist":
                            await self.callForAction("Ability:" + self.abilitiesList[self.fascistPolicies-1])
                        else: # successful team is Liberal - no ability activation
                            await self.resetGovernment(success)
                            await self.callForAction("Select Chancellor")




    async def setAbilities(self):
        if len(self.players.content) < 7: # a set of abilities
            """
            //nothing
            //nothing
            Policy Peek
            Execution
            Execution
            //victory
            """

            self.abilitiesList = ['Nothing', 'Nothing', 'PolicyPeek', 'Execute', 'Execute', 'Nothing']


        elif len(self.players.content) < 9: # a set of abilities
            """
            //nothing
            Investigation
            Special Election
            Execution
            Execution
            //victory
            """
            self.abilitiesList = ['Nothing', 'Investigate', 'SpecialElection', 'Execute', 'Execute', 'Nothing']


        else: # len is 9-10
            """
            Investigation
            Investigation
            Special Election
            Execution
            Execution
            //victory

            """
            self.abilitiesList = ['Investigate', 'Investigate', 'SpecialElection', 'Execute', 'Execute', 'Nothing']

    async def displayPowers(self):
        msg = "These are the powers at play, which the president can use if they pass a Fascist policy:\n\t"
        for power in self.abilitiesList:
            msg += power + "\n\t"
        self.client.send_message(self.channel, msg)


    #Presidential Powers
    async def policyPeek(self, player):

        await self.client.send_message(self.president.user, "The next three policies are {0[0]}, {0[1]}, and {0[2]}.".format(self.policyPile.content))

        # Proceed to select chancellor again - no action needed
        await self.resetGovernment(True)
        await self.callForAction("Select Chancellor")

    async def nothing(self, player):
        return #Does nothing. Placeholder in AbilityList

    async def investigate(self, player):
        await self.send_message(self.president.user, "{0} is a {1}.".format(player.user, player.team))

    async def specialElection(self, player):
        await self.resetGovernment(True)
        self.president = player
        self.callForAction("Select Chancellor: Special")

    async def execute(self, player):
        self.deadPlayers += [player]
        self.players.content.remove(player)
        #check if game over
        if self.hitler == player:
            self.inProgress = False
            self.awaitingAction = "None"
            await self.client.send_message(self.channel, "**Hitler has been killed! Liberals Win!** Start a new game by typing **sh-start**.")
        else:
            await self.resetGovernment(True)
            await self.callForAction("Select Chancellor")

    async def specialExecution(self, player):
        self.deadPlayers += [player]
        self.players.content.remove(player)
        #check if game over
        if self.hitler == player:
            self.inProgress = False
            self.awaitingAction = "None"
            await self.client.send_message(self.channel, "**Hitler has been killed! Liberals Win!** Start a new game by typing **sh-start**.")
        else:
            previousPresIndex = players.index(self.previousGovernment[0])
            await self.resetGovernment(True)
            self.president = players[previousPresIndex+1]
            await self.callForAction("Select Chancellor")

    async def veto(self, decision):
        if decision == True:
            self.discardPile.content += [self.policyPile.content.pop(0)]
            self.discardPile.content += [self.policyPile.content.pop(1)]
            previousPresident = self.previousGovernment[0]
            self.resetGovernment(False)
            self.callForAction("Select Chancellor")
        else:
            successfulTeam = self.policyPile.content.pop(0)
            if successfulTeam == "Liberal":
                self.liberalsPolicies += 1
            elif successfulTeam == "Fascist":
                self.fascistPolicies += 1
            self.checkGameOver()


    # async def resolveAbility(self, message):
    #     #we already know the user is the president, and they have typed "select ###########" with a user ID as the #s
    #     inputID = message.content.split(' ')[1]
    #     selectedPlayer = []
    #     for player in self.players.content:
    #         if player.user.id == inputID:
    #             selectedPlayer = player
    #             continue
    #     if selectedPlayer: #if a player was selected
    #         True #resolve ability according to list



    async def resetGovernment(self, success):

        previousPresident = self.previousGovernment[0]

        if success:
            self.previousGovernment = [self.president, self.chancellor]
            self.chaosTracker = 0
        elif self.chaosTracker > 2:
            await self.chaos()
            await self.displayTracks()
            await self.checkGameOver()

        if 'Special' in self.awaitingAction: #there must have been a previous government
            self.president = previousPresident

        self.president = self.players.content[(self.players.content.index(self.president) + 1) % len(self.players.content)]
        self.chancellor = 'none'

    async def chaos(self):
        self.chaosTracker = 0
        successfulTeam = self.policyPile.content.pop(0).team
        if successfulTeam == "Liberal":
            self.liberalPolicies += 1
        else: # Fascist
            self.fascistPolicies += 1
        await self.client.send_message(self.channel, "Chaos! A {0} policy has been added to the board.".format(successfulTeam))


    async def displayTracks(self):
        msg = "There are now {0}/{1} liberal policies, and {2}/{3} fascist policies. \nThe chaos tracker is at {4}".format(self.liberalPolicies, self.maxLiberals, self.fascistPolicies, self.maxFascists, self.chaosTracker)
        msg += "\nThere are {0} cards in the draw pile, and {1} cards in the discard pile.".format(len(self.policyPile.content), len(self.discardPile.content))
        await self.client.send_message(self.channel, msg)

    async def checkGameOver(self):
        if self.hitler in self.deadPlayers:
            self.inProgress = False
            self.awaitingAction = "None"
        elif self.liberalPolicies >= self.maxLiberals:
            self.inProgress = False
            self.awaitingAction = "None"
        elif self.fascistPolicies >= self.maxFascists:
            self.inProgress = False
            self.awaitingAction = "None"
        else:
            return "Resume"

    async def checkVotes(self):
        for player in self.players.content:
            if player.vote == 'none':
                return False
        await self.resolveVotes()

    async def resolveVotes(self):
        await self.addEvent("Votes Submitted")
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
            if await self.hitlerVictory():
                await self.client.send_message(self.channel,"Fascists Win! {0.mention} is a Hitler Chancellor after 3 Fascist policies were passed! \nStart a new game by typing **sh-start**.".format(self.chancellor.user))
                self.awaitingAction = 'none'
                self.inProgress = False
                return True #at thie point, the game ends

            #Move to discard phase
            #check if decks need to be combined
            await self.callForAction("President Discard")
            await self.revealPolicies("President")
        else:
            await self.failGovernment()

    async def hitlerVictory(self):
        if self.hitler == self.chancellor and self.fascistPolicies > 2:
            # TODO: return True
            return True


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


    async def failGovernment(self, type = 'default'):
        nextPresIndex = self.players.content.index(self.president) + 1 % len(self.players.content)
        self.president = self.players.content[nextPresIndex]
        chancellor = 'none'
        self.chaosTracker += 1
        await self.client.send_message(self.channel, "The government vote has failed. The chaos tracker is at {0}".format(self.chaosTracker))
        await self.resetGovernment(False)
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
            #TODO: This allows me to be a fascist for testing ->
            if len(self.fascists) < self.fascistsNumber:
                players[index].team = "Fascist"
                # We'll tell the fascists what they are later in this function
                self.fascists += [players.pop(index)]

            elif len(self.liberals) < self.liberalsNumber:
                players[index].team = "Liberal"
                await self.client.send_message(players[index].user, "You are a Liberal")
                self.liberals += [players.pop(index)]

        # Choose hitler. First player was chosen at random, so this is random
        self.hitler = self.fascists[0]

        # Tell fascists about their buddies
        msg = "The fascists are:\n\t"
        for p in self.fascists:
            msg += p.user.name + '\n\t'
        for p in [u for u in self.fascists if u != self.hitler]:
            await self.client.send_message(p.user,"You are a Fascist.\n" +  msg)
        # Only tell hitler who his allies are if there are
        if self.fascistsNumber < 7:
            await self.client.send_message(self.hitler.user, "You are Hitler.\n" + msg)
        else:
            await self.client.send_message(self.hitler.user, "You are Hitler. You have {0} other Fascist allies.".format(self.fascistNumber-1))



    async def isRecent(self):
        # Return false if game is idle for > 10 minutes
        return time.time() - self.events[-1][1] < shGame.gameTimeout

    async def addPlayer(self, message):

        if message.author not in [player.user for player in self.players.content]:
            if len(self.players.content) <= 10 or self.inProgress == True: #max players
                self.players.content += [Player(message.author, self)]
                await self.client.send_message(message.channel, "You have been added to the game.")
            else:
                await self.client.send_message(message.channel, "The game is full or in progress, you are being added as a spectator.")
            overwrite = discord.PermissionOverwrite()
            overwrite.read_messages = True
            overwrite.send_message = True
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
            self.players.content.remove([player for player in self.players.content if player.user == message.author][0])
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
        self.liberalsNumber = len(self.players.content) // 2 + 1
        self.fascistsNumber = len(self.players.content) - self.liberalsNumber



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
        numPolicies = len(self.content)
        for i in range(numPolicies):
            index = random.randint(0, len(self.content)-1)
            newPile += [self.content.pop(index)]
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
