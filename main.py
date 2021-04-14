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
    #intents.members = True

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

        embed = discord.Embed(title="Current {0} players in game:".format(clans),
                              description="--------------------", colour=discord.Colour.red())
        message = await ctx.send(embed=embed)

        while run:
            r = requests.get("https://api.dashlist.info/fetch")
            r = r.json()
            current = {}
            for server in r:
                if len(r[server]) > 6:
                    for player in r[server]['players']:
                        if player['tag'].lower() in clan_names:
                            if player['name'] not in blacklist:
                                if server in current:
                                    current[server].append(player)
                                else:
                                    current[server] = [player]

            embed = discord.Embed(title="Current {0} players in game:".format(clans),
                                  description="--------------------", colour=discord.Colour.blue())

            for server in current.items():
                players = ""
                blue = ""
                red = ""

                for player in server[1]:
                    if player['team'] == 0:
                        red += " :red_square: "
                        red += "[" + player['tag'] + "] " + player['name'] + " \n"
                    elif player['team'] == 1:
                        blue += " :blue_square: "
                        blue += "[" + player['tag'] + "] " + player['name'] + " \n"

                players += red + blue

                embed.add_field(name=server[0], value=players, inline=False)

            embed.set_footer(text="Made possible by Zed's API")

            await message.edit(embed=embed)
            time.sleep(1)

        await message.delete()
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
        """Sets the owner of the bot for this server. Owners can set the channel for use by the bot, start, and stop it."""
        global owner
        await ctx.message.delete()
        await ctx.send("Owner confirmed!", delete_after=2)
        owner = ctx.author.id

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
            time.sleep(2)
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
