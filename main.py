import sys
import os
import time
import discord
from discord.ext import commands
import requests
import datetime
import threading

if __name__ == "__main__":
    description = "Dash Clan Peeper"

    token = ""

    intents = discord.Intents.default()

    bot = commands.Bot(command_prefix="!", description=description, intents=intents)
    client = discord.Client()

    loadedtime = 0

    r = ""
    owner = ""
    run = False
    blacklist = []


    async def update(ctx, clan_names):

        print("Running update thread...")
        global r
        clans = ""
        for clan in clan_names:
            clans += clan + " "

        clanembed = discord.Embed(title="Currently online {0} players:".format(clans), colour=discord.Colour.blue())

        message = await ctx.send(embed=clanembed)

        while run:
            r = requests.get("https://api.dashlist.info/fetch")
            r = r.json()
            current = {}
            for server in r:
                player_num = 0
                if len(r[server]) > 6:
                    for player in r[server]['players']:
                        player_num += 1
                        if player['tag'].lower() in clan_names:
                            if player['name'] not in blacklist:
                                if server in current:
                                    current[server].append(player)
                                else:
                                    current[server] = [player]
                            current[server].append(player_num)

            if len(current.items()) > 0:

                clanembed = discord.Embed(title="Currently online {0} players:".format(clans),
                                          colour=discord.Colour.blue())

                for server in current.items():
                    players = ""
                    blue = ""
                    red = ""
                    player_num = 0

                    for player in server[1]:
                        if type(player) != int:
                            if player['team'] == 0:
                                red += " :red_square: "
                                red += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 1:
                                blue += " :blue_square: "
                                blue += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 2:
                                players += " :yellow_square: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 3:
                                players += " :green_square: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 4:
                                players += " :purple_square: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 5:
                                players += " :orange_square: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 6:
                                players += " :black_large_square: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 7:
                                players += " :white_large_square: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 8:
                                players += " :blue_circle: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 9:
                                players += " :purple_circle: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            elif player['team'] == 10:
                                players += " :black_square_button: "
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                            else:
                                players += "[" + player['tag'] + "] " + player['name'] + " \n"
                        else:
                            player_num = player

                    players += red + blue
                    name = str(server[0]) + " [{0}/10]".format(player_num)
                    if len(name) > 0 and len(players) > 0:
                        clanembed.add_field(name=name, value=players, inline=False)
            else:
                clanembed = discord.Embed(title="Currently online {0} players:".format(clans),
                                          colour=discord.Colour.red())
                clanembed.add_field(name="None Online", value = "No players are online currently...")

            await message.edit(embed=clanembed)
            time.sleep(1)
        return


    @bot.event
    async def on_ready():
        global loadedTime
        global r
        loadedTime = datetime.datetime.now()
        print("Logged in as: " + bot.user.name + " " + str(bot.user.id))
        print("Time loaded: {0}".format(str(loadedTime)[:-7]))
        print("----\n")

        try:
            r = requests.get("https://api.dashlist.info/fetch")
            r = r.json()
        except:
            print("Request failed... Cancelling bot!")
            sys.exit()


    @bot.command()
    async def owner(ctx):
        """Sets the owner of the bot for this server. Owners can set the channel for use by the bot, start,
        and stop it. """
        global owner
        if owner != "":
            await ctx.message.delete()
            await ctx.send("Owner confirmed!", delete_after=2)
            owner = ctx.author.id
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")

    @bot.command()
    async def run(ctx, *clan_names):
        """Starts the bot searching for online clan members. Clan types should be inputted with spaces in-between."""
        if ctx.author.id == owner:
            global run
            names = []
            for name in clan_names:
                names.append(name)
            await ctx.message.delete()
            await ctx.send("Running! Finding people of clans {0}".format(clan_names), delete_after=2)
            run = True
            await update(ctx, clan_names)
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")

    @bot.command()
    async def optout(ctx, name):
        """Opts you out of the tracking whilst this instance of bot is active. NOTE: Does not prevent tracking
        indefinitely. """
        blacklist.append(name)
        await ctx.message.delete()
        await ctx.send("You have blacklisted {0} from the tracking of DashClanPeeper.".format(name), delete_after=2)
        await ctx.send("Please note, in this current version, this does not eliminate the user from tracking forever, "
                       "only whilst the current bot instance is running.", delete_after=5)

    @bot.command()
    async def optin(ctx, name):
        """Opts somebody back into tracking, if you have the privileges."""
        if ctx.author.id == owner:
            blacklist.remove(name)
            await ctx.message.delete()
            await ctx.send("You have removed {0} from the blacklist of DashClanPeeper.".format(name), delete_after=2)
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def ping(ctx):
        """Returns the latency of this bot!"""
        if ctx.author.id == owner:
            await ctx.send("My current response time is: {0}ms".format(round(bot.latency, 1)))
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def uptime(ctx):
        """Returns the uptime of the bot as seconds."""
        if ctx.author.id == owner:
            elapsed = datetime.datetime.now() - loadedTime
            await ctx.send("Bot has been active for: {0} days, {1} hours, and {2} minutes.".format(
                str(elapsed.days), str(round(elapsed.seconds / 3600)), str(round(elapsed.seconds / 60))))
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")

    @bot.command()
    async def stop(ctx):
        """Stops the bot, if you have the right."""
        if ctx.author.id == 344911466195058699 or ctx.author.id == owner:
            global run
            await ctx.send("Stopping", delete_after=2)
            await ctx.message.delete()
            run = False
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    bot.run(token)
