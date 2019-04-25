# Secret-Hitler-Bot

A bot which allows users to play secret hitler.

# Before use:
Insert your bot token at the bottom of the myBot.py file.
The bot must be given the following permissions in-server in order to work properly: 
    Read/see channels (enabled by default),
    send messages (enabled by default),
    **manage channels,** 
    **manage roles.** 
    
Notes:

* The sh-game class contains a timeout variable. Change this in order to allow non-admin users to restart the game after players have been afk for a duration longer than said variable, in seconds.

* 5 players minimum per game, 10 players maximum (as per Secret Hitler rules)

* There is a max of one game per server, by default. This prevents the server from appearing cluttered to users who can see all channels at once. If you change this, you'll have to change several functions as to prevent all games and secret-hitler-game channels in a server from being deleted once a new game is started.

* I (the bot) must be given the following permissions, on a per-server basis, in order to work properly: Read/see channels, **manage channels**, **manage roles**, send messages.

* How to play Secret Hitler: https://www.ultraboardgames.com/secret-hitler/game-rules.php'''

    
