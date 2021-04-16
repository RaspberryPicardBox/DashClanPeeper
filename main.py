import asyncio
import json
import sys
import os
import threading
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
    blacklist = []

    servers = {}

    emojis = [" :red_square: ", " :blue_square: ", " :yellow_square: ", " :green_square: ", " :purple_square: ",
              ":orange_square: ", " :black_large_square: ", " :white_large_square: ", " :blue_circle: ",
              " :purple_circle: ", " :black_square_button: "]  # Thank you for the idea Titan1315


    async def update(ctx, clan_names):

        print("Running update thread in {0}...".format(ctx.message.guild.id))

        global r

        clan_names = [clan.lower() for clan in clan_names]
        clanprint = ""
        for clan in clan_names:
            clanprint += " [" + clan.upper() + "]"

        clanembed = discord.Embed(title="Filtering by{0}".format(clanprint), colour=discord.Colour.red())

        message = await ctx.send(embed=clanembed)

        while servers[ctx.message.guild.id][0]:
            try:
                r = requests.get("https://api.dashlist.info/fetch").json()

                current = {}
                clanembed = discord.Embed(title="Filtering by{0}".format(clanprint), colour=discord.Colour.blue())

                for server in r:
                    if "players" in r[server]:
                        for player in r[server]['players']:
                            if player['tag'].lower() in clan_names:
                                if player['name'] not in blacklist:
                                    if server not in current:
                                        current[server] = [player]
                                    else:
                                        current[server].append(player)
                                elif player['name'] in blacklist:
                                    if server in current:
                                        if player['name'] in current[server]:
                                            current[server].remove(player['name'])
                                if server in current:
                                    current[server].append(len(r[server]['players']))

                if len(current.items()) > 0:
                    for info in current.items():
                        players = ""
                        player_num = ""
                        for player in info[1]:
                            if type(player) != int:
                                players += "{0} **{1}** {2}\n".format(emojis[player['team']], player['tag'],
                                                                      player['name'])
                            else:
                                player_num = player

                        clanembed.add_field(name=info[0] + " [{0}/10]".format(player_num), value=players)
                else:
                    clanembed.colour = discord.Colour.red()
                    clanembed.add_field(name="No players online...", value="No players online from clans{0}".format(
                        clanprint))

                clanembed.set_footer(text="Bot made by RaspiBox. Made possible thanks to Zed's API.\nTime of last "
                                          "update: {0}".format(str(datetime.datetime.now())[:-7]))
                await message.edit(embed=clanembed)
                await asyncio.sleep(5)
            except ValueError:
                clanembed.description = "***ERROR:*** Error retrieving Dash List data..."
                clanembed.colour = discord.Colour.red()
                await message.edit(embed=clanembed)
                await asyncio.sleep(5)
                pass

        print("Update thread stopping...")
        await message.delete()
        return


    def get_json(filename):
        with open("{0}".format(filename)) as f:
            contents = json.load(f)
        f.close()
        return contents


    def set_json(filename, contents):
        with open("{0}".format(filename), "a") as f:
            f.truncate(0)
            f.write(json.dumps(contents))
        f.close()


    def update_blacklist(ctx, user, remove):
        global blacklist

        contents = get_json("blacklist_global.json")

        if remove:
            if str(ctx.message.guild.id) in contents:
                if user not in contents[str(ctx.message.guild.id)]:
                    contents[str(ctx.message.guild.id)] += [user]
            else:
                contents[str(ctx.message.guild.id)] = [user]
        else:
            if str(ctx.message.guild.id) in contents:
                if user in contents[str(ctx.message.guild.id)]:
                    contents[str(ctx.message.guild.id)].remove(user)

        set_json("blacklist_global.json", contents)

        blacklist = contents[str(ctx.message.guild.id)]
        return True


    @bot.event
    async def on_ready():
        global loadedTime
        global r
        try:
            get_json("blacklist_global.json")
        except FileNotFoundError:
            f = open("blacklist_global.json", "a")
            f.write("{}")
            f.close()
        loadedTime = datetime.datetime.now()
        print("Logged in as: " + bot.user.name + " " + str(bot.user.id))
        print("Time loaded: {0}".format(str(loadedTime)[:-7]))
        print("----\n")


    @bot.command()
    async def owner(ctx):
        """Sets the owner of the bot for this server. Owners can set the channel for use by the bot, start,
        and stop it. """
        global owner
        global blacklist
        global servers
        if owner != "":
            servers[ctx.message.guild.id] = [False, "", ""]
            servers[ctx.message.guild.id][1] = ctx.author.id
            contents = get_json("blacklist_global.json")
            if str(ctx.message.guild.id) in contents:
                blacklist = contents[str(ctx.message.guild.id)]
            await ctx.message.delete()
            await ctx.send("Owner confirmed!", delete_after=2)
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def run(ctx, *clan_names):
        """Starts the bot searching for online clan members. Clan types should be inputted with spaces in-between."""
        try:
            if ctx.author.id == servers[ctx.message.guild.id][1]:
                await ctx.message.delete()
                await ctx.send("Running! Finding people of clans {0}".format(clan_names), delete_after=2)
                servers[ctx.message.guild.id][0] = True
                if str(clan_names) not in servers[ctx.message.guild.id][2]:
                    servers[ctx.message.guild.id][2] += str(clan_names)
                await update(ctx, clan_names)
            else:
                await ctx.send("Sorry, but you don't have the privileges to do that!")
        except KeyError:
            await ctx.send("No owner has been assigned yet. `!help owner` for more info.")


    @bot.command()
    async def optout(ctx, name):
        """Opts you out of the tracking whilst this instance of bot is active. NOTE: Does not prevent tracking
        indefinitely. """
        await ctx.message.delete()
        accomplished = update_blacklist(ctx, name, True)
        if accomplished:
            await ctx.send("You have blacklisted {0} from the tracking of DashClanPeeper.".format(name), delete_after=5)
        else:
            await ctx.send("Something went wrong when attempting to blacklist {0}.".format(name), delete_after=5)


    @bot.command()
    async def optin(ctx, name):
        """Opts somebody back into tracking, if you have the privileges."""
        try:
            if ctx.author.id == servers[ctx.message.guild.id][1]:
                await ctx.message.delete()
                accomplished = update_blacklist(ctx, name, False)
                if accomplished:
                    await ctx.send("You have removed {0} from the blacklist of DashClanPeeper.".format(name),
                                   delete_after=5)
                else:
                    await ctx.send("Something went wrong when trying to remove {0} from the blacklist.".format(name),
                                   delete_after=5)
            else:
                await ctx.send("Sorry, but you don't have the privileges to do that!")
        except KeyError:
            await ctx.send("No owner has been assigned yet. `!help optin` for more info.")


    @bot.command()
    async def ping(ctx):
        """Returns the latency of this bot!"""
        if ctx.author.id == servers[ctx.message.guild.id][1]:
            await ctx.send("My current response time is: {0}ms".format(round(bot.latency, 1)))
            await ctx.send(servers)
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def uptime(ctx):
        """Returns the uptime of the bot as seconds."""
        if ctx.author.id == servers[ctx.message.guild.id][1]:
            elapsed = datetime.datetime.now() - loadedTime
            await ctx.send("Bot has been active for: {0} days, {1} hours, and {2} minutes.".format(
                str(elapsed.days), str(round(elapsed.seconds / 3600)), str(round(elapsed.seconds / 60))))
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def stop(ctx):
        """Stops the bot tracking, if you have the right."""
        if ctx.author.id == 344911466195058699 or ctx.author.id == servers[ctx.message.guild.id][1]:
            servers[ctx.message.guild.id][0] = False
            await ctx.send("Stopping", delete_after=2)
            await ctx.message.delete()
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def reset(ctx):
        """Resets the bot's tracking log (clans being tracked), if you have the right."""
        if ctx.author.id == 344911466195058699 or ctx.author.id == servers[ctx.message.guild.id][1]:
            servers[ctx.message.guild.id][0] = False
            servers[ctx.message.guild.id][2] = ""
            await ctx.send("Resetting log!", delete_after=2)
            await ctx.message.delete()
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def total_reset(ctx):
        """Resets the bot's tracking log completely and globally (clans being tracked and blacklist), if you have the
        right."""
        if ctx.author.id == 344911466195058699:
            servers = []
            blacklist = []
            set_json("blacklist_global.json", {})
            await ctx.send("Resetting entire bot logs!", delete_after=2)
            await ctx.message.delete()
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    bot.run(token)
