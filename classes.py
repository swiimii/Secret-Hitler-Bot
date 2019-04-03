import discord
import random

class shGame:
    gameServers = []


    # def __init__(self,client,firstPlayer,server,startedChannel):
    #     shGame.gameServers += [self]
    #     self.inProgress = True
    #     self.channel = startedChannel
    #     self.server = server
    #     self.players = [firstPlayer]
    #     self.fascists = []
    #     self.liberals = []
    #     self.events = []
    #     self.client = client
    def __init__(self,client,message,channel):
        shGame.gameServers += [self]
        self.inProgress = True
        self.channel = channel
        self.server = message.server
        self.players = [message.author]
        self.fascists = []
        self.liberals = []
        self.events = []
        self.client = client


    async def addPlayer(self,player):
        self.players += [player]

    async def definePlayerRatios(self):
        fascistsNumber = len(players) // 2 - 1
        liberalsNumber = len(players) - fascistsNumber
        # Randomly add a number of players to each team, according to these ratios

    async def announceGame(self,message):
        announcemsg = """A Secret Hitler game is starting! \nType '!sh-join' to join in! """
        await self.client.send_message(message.channel,announcemsg)
        newgamemsg = """Welcome to Secret Hitler, \nOnce everybody's in, type \n'!sh-start' to start the game! """
        await self.client.send_message(self.channel,newgamemsg)
