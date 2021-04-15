import asyncio
import sys
import os
import time
import discord
from discord.ext import commands
import requests
import datetime

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

    emojis = [" :red_square: ", " :blue_square: ", " :yellow_square: ", " :green_square: ", " :purple_square: ",
              ":orange_square: ", " :black_large_square: ", " :white_large_square: ", " :blue_circle: ",
              " :purple_circle: ", " :black_square_button: "]


    async def update(ctx, clan_names):

        print("Running update thread...")

        global r

        clan_names = [clan.lower() for clan in clan_names]
        clanprint = ""
        for clan in clan_names:
            clanprint += " [" + clan.upper() + "]"

        clanembed = discord.Embed(title="Filtering by{0}".format(clanprint), colour=discord.Colour.red())

        message = await ctx.send(embed=clanembed)

        while run:
            r = requests.get("https://api.dashlist.info/fetch").json()

            current = {}
            clanembed = discord.Embed(title="Filtering by{0}".format(clanprint), colour=discord.Colour.blue())

            for server in r:
                if len(r[server]) > 5:
                    for player in r[server]['players']:
                        if player['tag'].lower() in clan_names:
                            if player['name'] not in blacklist:
                                if server not in current:
                                    current[server] = [player]
                                else:
                                    current[server].append(player)
                            current[server].append(len(r[server]['players']))

            if len(current.items()) > 0:
                for info in current.items():
                    players = ""
                    player_num = ""
                    for player in info[1]:
                        if type(player) != int:
                            players += "{0} [{1}] {2}\n".format(emojis[player['team']], player['tag'], player['name'])
                        else:
                            player_num = player

                    clanembed.add_field(name=info[0] + " [{0}/10]".format(player_num), value=players)
            else:
                clanembed.colour = discord.Colour.red()
                clanembed.add_field(name="No players online...", value="No players online from clans{0}".format(
                    clanprint))

            clanembed.set_footer(text="Bot made by [DARK] RaspiBox. Made possible thanks to Zed's API.\nTime of last "
                                      "update: {0}".format(str(datetime.datetime.now())[:-7]))
            await message.edit(embed=clanembed)
            await asyncio.sleep(5)

        print("Update thread stopping...")
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
