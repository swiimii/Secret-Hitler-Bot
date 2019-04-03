import discord
import random

class secretHitlerGame:
    serversRunningGame = []
    players = []
    fascists = []
    liberals = []
    events = []


    def __init__(self,client,firstPlayer,server,startedChannel):
        addPlayer[firstPlayer]
        serversRunningGame += [server]
        announceGame(channel)


    def addPlayer(self,player):
        players += [player]

    def definePlayerRatios(self):
        fascistsNumber = len(players) // 2 - 1
        liberalsNumber = len(players) - fascistsNumber

    def announceGame(client, channel):
        msg = """---------------------------------\n
        A Secret Hitler game is starting! \n
        Type !shb-join to join in! \n
        ---------------------------------"""
        await client.send_message(channel, msg)
