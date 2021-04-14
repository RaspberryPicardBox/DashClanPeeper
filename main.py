import sys
import os
import time
import discord
from discord.ext import commands
import requests
import datetime
import threading

if __name__ == "__main__":
    description = "Clan Currently Playing Bot"

    token = "token"

    intents = discord.Intents.default()
    #intents.members = True

    bot = commands.Bot(command_prefix="!", description=description, intents=intents)
    client = discord.Client()

    r = ""

    loadedtime = 0
    owner = ""
    channel = ""
    run = False


    async def update(ctx, clan_names):

        print("Running update thread...")
        global r
        clans = ""
        for clan in clan_names:
            clans += clan + " "

        embed = discord.Embed(title="Current {0} Players in Game".format(clans),
                              description="Current players online...", colour=discord.Colour.red())
        message = await ctx.send(embed=embed)

        while run:
            r = requests.get("https://api.dashlist.info/fetch")
            r = r.json()
            current = {}
            for server in r:
                if len(r[server]) > 5:
                    for player in r[server]['players']:
                        if player['tag'].lower() in clan_names:
                            if server in current:
                                current[server].append(player)
                            else:
                                current[server] = [player]

            embed = discord.Embed(title="Current {0} Players in Game".format(clans),
                                  description="Current players online...", colour=discord.Colour.blue())
            for server in current.items():
                players = ""

                for player in server[1]:
                    players += "[" + player['tag'] + "] " + player['name'] + "\n"

                embed.add_field(name=server[0], value=players, inline=False)

            await message.edit(embed=embed)
            time.sleep(1)


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
    async def here(ctx):
        """Gives the bot a channel to work in."""
        global channel
        if ctx.author.id == owner:
            await ctx.send("Confirmed! Bot will work here...", delete_after=2)
            await ctx.message.delete()
            channel = ctx.message.channel.id
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
            time.sleep(2)
            await update(ctx, clan_names)
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
    async def restart(ctx):
        """Restarts the bot, if you have the right."""
        if ctx.author.id == 344911466195058699 or ctx.author.id == owner:
            await ctx.send("Restarting the bot...")
            print("Bot restart initiated!")
            await bot.close()
            print("Current bot closed...")
            print("New instance being created!\n")
            await os.system("python3 bot.py")
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def stop(ctx):
        """Stops the bot, if you have the right."""
        if ctx.author.id == 344911466195058699 or ctx.author.id == owner:
            await ctx.send("Shutting down...")
            print("Bot shutting down...\n")  #
            await bot.close()
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    bot.run(token)
