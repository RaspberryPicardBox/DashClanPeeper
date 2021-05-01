import asyncio
import datetime
import json
from datetime import timezone

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, MissingRequiredArgument
import dash

if __name__ == "__main__":
    description = "Dash Clan Peeper"

    token = ""

    intents = discord.Intents.default()

    bot = commands.Bot(command_prefix="!", description=description, intents=intents)
    client = discord.Client()

    loadedtime = 0

    blacklist = []

    servers = {}

    emojis = [" :red_square: ", " :blue_square: ", " :yellow_square: ", " :green_square: ", " :purple_square: ",
              ":orange_square: ", " :black_large_square: ", " :white_large_square: ", " :blue_circle: ",
              " :purple_circle: ", " :black_square_button: "]  # Thank you for the idea Titan1315


    async def get_json(filename):
        with open("{0}".format(filename)) as f:
            contents = json.load(f)
        f.close()
        return contents


    async def set_json(filename, contents):
        with open("{0}".format(filename), "a") as f:
            f.truncate(0)
            f.write(json.dumps(contents))
        f.close()


    async def update_blacklist(user, remove):
        global blacklist

        contents = await get_json("blacklist_global.json")

        if remove:
            if user not in contents:
                contents.append(user)
        else:
            if user in contents:
                contents.remove(user)

        await set_json("blacklist_global.json", contents)

        blacklist = contents
        return True


    async def update(ctx, clan_names):
        cont = True
        current_tags = []

        clan_names = [clan.lower() for clan in clan_names]
        clanprint = ""
        for clan in clan_names:
            clanprint += " [" + clan.upper() + "]"

        clanembed = discord.Embed(title="Filtering by{}".format(clanprint))

        message = await ctx.send(embed=clanembed)

        while servers[ctx.message.guild.id][ctx.message.channel.id][ctx.message.id][0]:
            clanembed = discord.Embed(title="Filtering by{}".format(clanprint))

            try:
                current_tags = dash.get_server_player_by_tag(clan_names)
                clanembed.colour = discord.Colour.blue()
            except KeyError:
                cont = False
                clanembed.colour = discord.Colour.red()

            if cont:
                for server in current_tags:
                    levels = []
                    players = current_tags[server]
                    tag_players = ""
                    non_tag_players = ""
                    for player in players:
                        tag_players += "{} ***{}*** {}\n".format(emojis[player.team], player.tag, player.name)
                        levels.append(player.level)
                    for player in server.players:
                        if player not in players:
                            non_tag_players += "{} {} {}\n".format(emojis[player.team], player.tag, player.name)
                            levels.append(player.level)
                    average = round(sum(levels) / len(levels))
                    clanembed.add_field(
                        name="{} [{}/10] *Average Level: {}*".format(server.name, len(server.players), average),
                        value="{0} {1}".format(tag_players, non_tag_players))

                clanembed.set_footer(text="Bot made by RaspiBox. Made possible thanks to Zed's API.\nTime of last "
                                          "update: {0} UTC".format(str(datetime.datetime.now(timezone.utc))[:-13]))

                await message.edit(embed=clanembed)
                await asyncio.sleep(5)

            else:
                clanembed.add_field(name="Unable to get data from Zed's API!", value="Please contact RaspiBox for "
                                                                                      "assistance.")
                await message.edit(embed=clanembed)
                return

        await message.delete()
        return


    @bot.event
    async def on_ready():
        global loadedTime
        try:
            await get_json("blacklist_global.json")
        except FileNotFoundError:
            f = open("blacklist_global.json", "a")
            f.write("[]")
            f.close()
        try:
            await get_json("servers.json")
        except FileNotFoundError:
            f = open("servers.json", "a")
            f.write("{}")
            f.close()
        if not dash.update():
            print("WARNING: CANNOT ACCESS ZED'S API")
        loadedTime = datetime.datetime.now()
        print("Logged in as: " + bot.user.name + " " + str(bot.user.id))
        print("Time loaded: {0}".format(str(loadedTime)[:-7]))
        print("----\n")


    @bot.command()
    @has_permissions(manage_messages=True)
    async def run(ctx, *clan_names):
        """Starts the bot searching for online clan members. Clan types should be inputted with spaces in-between."""
        global servers

        await ctx.message.delete()
        if len(clan_names) > 0:
            await ctx.send("Tracking clans: {}".format(clan_names), delete_after=2)

            try:
                servers[ctx.message.guild.id][ctx.message.channel.id][ctx.message.id] = [True, clan_names]
            except KeyError:
                try:
                    servers[ctx.message.guild.id][ctx.message.channel.id] = {ctx.message.id: [True, clan_names]}
                except KeyError:
                    servers[ctx.message.guild.id] = {ctx.message.channel.id: {ctx.message.id: [True, clan_names]}}

            client.loop.create_task(update(ctx, clan_names))
        else:
            await ctx.send("Sorry, but you must input a clan name to be tracked!", delete_after=5)


    @bot.command()
    @has_permissions(manage_messages=True)
    async def stop(ctx):
        """Stops the bot tracking in the current channel, if you have the right."""
        global servers

        await ctx.message.delete()
        await ctx.send("Stopping tracking in channel...", delete_after=2)

        try:
            for message in servers[ctx.message.guild.id][ctx.message.channel.id]:
                servers[ctx.message.guild.id][ctx.message.channel.id][message][0] = False
        except KeyError:
            await ctx.send("Sorry, but it looks like there aren't any clans currently being tracked in this channel!",
                           delete_after=5)


    @bot.command()
    async def lobby(ctx, name):
        """Returns a list of players in whatever server the named player is in"""
        name_embed = discord.Embed(title="Finding player {}".format(name))

        message = await ctx.send(embed=name_embed)

        cont = True
        current_name = []

        try:
            current_name = dash.get_server_player_by_name(name)
            name_embed.colour = discord.Colour.blue()
        except KeyError:
            cont = False
            name_embed.colour = discord.Colour.red()

        if cont:
            for server in current_name:
                levels = []
                players = current_name[server]
                tag_players = ""
                non_tag_players = ""
                for player in players:
                    tag_players += "{} ***{}*** {}\n".format(emojis[player.team], player.tag, player.name)
                    levels.append(player.level)
                for player in server.players:
                    if player not in players:
                        non_tag_players += "{} {} {}\n".format(emojis[player.team], player.tag, player.name)
                        levels.append(player.level)
                average = round(sum(levels) / len(levels))
                name_embed.add_field(
                    name="{} [{}/10] *Average Level: {}*".format(server.name, len(server.players), average),
                    value="{0} {1}".format(tag_players, non_tag_players))

            name_embed.set_footer(text="Bot made by RaspiBox. Made possible thanks to Zed's API.\nTime of "
                                       "update: {0} UTC".format(str(datetime.datetime.now(timezone.utc))[:-13]))

            await message.edit(embed=name_embed)
        else:
            name_embed.add_field(name="Unable to get data from Zed's API!", value="Please contact RaspiBox for "
                                                                                  "assistance.")
            await message.edit(embed=name_embed)


    @bot.command()
    async def optout(ctx, name):
        """Opts you out of the tracking whilst this instance of bot is active. NOTE: Whilst in alpha, does not prevent
        tracking indefinitely. """
        await ctx.message.delete()
        accomplished = update_blacklist(name, True)
        if accomplished:
            await ctx.send("You have blacklisted {0} from the tracking of DashClanPeeper.".format(name), delete_after=5)
        else:
            await ctx.send("Something went wrong when attempting to blacklist {0}.".format(name), delete_after=5)


    @bot.command()
    @has_permissions(manage_messages=True)
    async def optin(ctx, name):
        """Opts somebody back into tracking, if you have the privileges."""
        await ctx.message.delete()
        accomplished = update_blacklist(name, False)
        if accomplished:
            await ctx.send("You have removed {0} from the blacklist of DashClanPeeper.".format(name),
                           delete_after=5)
        else:
            await ctx.send("Something went wrong when trying to remove {0} from the blacklist.".format(name),
                           delete_after=5)


    @bot.command()
    async def ping(ctx):
        """Returns the latency of this bot!"""
        await ctx.send("My current response time is: {0}ms".format(round(bot.latency, 1)))


    @bot.command()
    async def uptime(ctx):
        """Returns the uptime of the bot as seconds."""
        elapsed = datetime.datetime.now() - loadedTime
        await ctx.send("Bot has been active for: {0} days, {1} hours, and {2} minutes.".format(
            str(elapsed.days), str(round(elapsed.seconds / 3600)), str(round(elapsed.seconds / 60))))


    @bot.command()
    async def total_reset(ctx):
        """Resets the bot's tracking log completely and globally (clans being tracked and blacklist), if you have the
        right."""
        if ctx.author.id == 344911466195058699:
            global servers
            global blacklist
            servers = {}
            blacklist = []
            await set_json("blacklist_global.json", [])
            await set_json("servers.json", {})
            await ctx.send("Resetting entire bot logs!", delete_after=2)
            await ctx.message.delete()
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @run.error
    @lobby.error
    @optout.error
    @optin.error
    @stop.error
    async def permission_error(ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("Sorry, but you do not have the permissions to do that.", delete_after=5)
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send("You have neglected to add in an argument after the command. Please use !help.",
                           delete_after=5)


    bot.run(token)
