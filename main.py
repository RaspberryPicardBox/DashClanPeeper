import asyncio
import datetime
import json
import sys
import logging
from datetime import timezone

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, MissingRequiredArgument, PrivateMessageOnly
from discord import NotFound
import dash
from aiohttp import ServerConnectionError

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
logging.basicConfig(filename="dashPeepLogs.log")

log = open("dashPeepLogs.log", "a")
log.truncate(0)
log.close()


def handle_exception(exc_type, exc_value, exc_traceback):  # Thanks to Dennis Golomazov on Stack Overflow
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("{} Uncaught exception".format(datetime.datetime.now()), exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

if __name__ == "__main__":
    description = "Dash Clan Peeper"

    token = ""

    intents = discord.Intents.default()

    bot = commands.Bot(command_prefix="!", description=description, intents=intents)
    client = discord.Client()

    session: object

    loadedtime = 0
    tasks = []

    blacklist = []
    servers = {}
    friends_list = {}
    mute_list = {}

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


    async def update(guild_id, channel_id, message_id, message=None):
        cont = True
        current_tags = []

        try:
            clan_names = servers[guild_id][channel_id][message_id][1]
        except KeyError:
            return

        clan_names = [clan.lower() for clan in clan_names]
        clanprint = ""
        for clan in clan_names:
            clanprint += " [" + clan.upper() + "]"

        clanembed = discord.Embed(title="Filtering by{}".format(clanprint))

        if message is None:
            try:
                channel = bot.get_channel(channel_id)
                message = await channel.fetch_message(int(message_id))
            except NotFound:
                servers[guild_id][channel_id][message_id][0] = False

        try:
            while servers[guild_id][channel_id][message_id][0]:
                clanembed = discord.Embed(title="Filtering by{}".format(clanprint))

                try:
                    current_tags = await dash.get_server_player_by_tag(session, clan_names)
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
                            tag_players += "{} **{} {}** *[{}]*\n".format(emojis[player.team], player.tag, player.name, player.level)
                            levels.append(player.level)
                        for player in server.players:
                            if player not in players:
                                non_tag_players += "{} {} {} *[{}]*\n".format(emojis[player.team], player.tag, player.name, player.level)
                                levels.append(player.level)
                        average = round(sum(levels) / len(levels))
                        if server.password:
                            password = ":lock:"
                        else:
                            password = ":unlock:"
                        clanembed.add_field(
                            name="{} [{}/10] Average Level: {}\nCurrently playing: {}"
                                 "\nPass: {}".format(server.name, len(server.players), average, server.mode, password),
                            value="{0} {1}".format(tag_players, non_tag_players), inline=False)

                    clanembed.set_footer(text="Bot made by RaspiBox. Made possible thanks to Zed's API.\nTime of last "
                                              "update: {0} UTC".format(str(datetime.datetime.now(timezone.utc))[:-13]))

                    await message.edit(embed=clanembed, content=None)
                    await asyncio.sleep(5)

                else:
                    clanembed.add_field(name="Unable to get data from Zed's API, or bot has been reset!",
                                        value="Please contact RaspiBox for assistance.")
                    await message.edit(embed=clanembed)
                    servers[guild_id][channel_id][message_id][0] = False
                    await set_json("servers.json", servers)
                    return
        except KeyError:
            clanembed.colour = discord.Colour.red()
            clanembed.add_field(name="Bot has been reset!", value="Please contact RaspiBox for assistance, or delete "
                                                                  "this message if intentionally stopped.")
            await message.edit(embed=clanembed)
            return

        clanembed = discord.Embed(title="Tracking has stopped!", colour=discord.Colour.gold())
        clanembed.add_field(name="Tracking temporarily halted...", value="Contact server admins to resume tracking.")
        await message.edit(embed=clanembed)
        return


    async def friends_update(user_id):
        global mute_list
        cont = True
        online_now = []
        user = await bot.fetch_user(user_id)
        try:
            muted = mute_list[user_id]
        except KeyError:
            mute_list[user_id] = 0
        try:
            track = friends_list[user_id]
            names = [name.lower() for name in track]
            while len(friends_list[user_id]) > 0:
                if mute_list[user_id] == 0:
                    for friend in track:
                        online = await dash.get_server_player_by_name(session, friend)
                        if friend not in online_now and len(online) > 0:
                            online_now.append(friend)
                            for server in online:
                                if len(server.players) < 10:
                                    send_embed = discord.Embed(title="{} is online now in {}! There are {} people "
                                                                     "playing currently.".format(friend, server.name,
                                                                                                 len(server.players)),
                                                               description="Use !lobby {} to get more info, or !mute ["
                                                                           "number] to mute notifications for a "
                                                                           "certain amount of hours.".format(
                                                                            friend), colour=discord.Colour.blue())
                                    await user.send(embed=send_embed)
                        else:
                            if len(online) == 0:
                                if friend in online_now:
                                    online_now.remove(friend)
                else:
                    if (mute_list[user_id] - 30) > 0:
                        mute_list[user_id] -= 30
                    else:
                        mute_list[user_id] = 0
                await asyncio.sleep(30)
            cont = False
        except KeyError:
            print("KEY ERROR")
            cont = False
        return


    @bot.event
    async def on_ready():
        global loadedTime
        global servers
        global tasks
        global session
        try:
            await get_json("blacklist_global.json")
            print("Found blacklist...\n")
        except FileNotFoundError:
            f = open("blacklist_global.json", "a")
            f.write("[]")
            f.close()
            print("Did not find blacklist, creating new...\n")
        try:
            content = await get_json("servers.json")
            for server in content:
                for channel in content[str(server)]:
                    for message in content[server][channel]:
                        servers[int(server)] = {int(channel): {int(message): content[server][channel][message]}}
                        if content[server][channel][message][0]:
                            print("Running update {}".format(message))
                            client.loop.create_task(update(int(server), int(channel), int(message))) \
                                .set_name("Update{}".format(message))
            print("Found server list...\n")
        except FileNotFoundError:
            f = open("servers.json", "a")
            f.write("{}")
            f.close()
            print("Did not find server list, creating new...\n")
        try:
            content = await get_json("friends.json")
            for player in content:
                for friend in content[player]:
                    try:
                        friends_list[int(player)].append(friend)
                    except KeyError:
                        friends_list[int(player)] = [friend]
                client.loop.create_task(friends_update(int(player)))
            print("Found friends list...\n")
        except FileNotFoundError:
            f = open("friends.json", "a")
            f.write("{}")
            f.close()
            print("Did not find friends list, creating new...\n")
        try:
            session = await dash.get_session()
            await dash.update(session)
        except ServerConnectionError:
            print("UNABLE TO CONNECT TO ZED'S API")
            raise ServerConnectionError
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
            message = await ctx.send("Please wait...")

            try:
                servers[ctx.message.guild.id][ctx.message.channel.id][message.id] = [True, clan_names]
            except KeyError:
                try:
                    servers[ctx.message.guild.id][ctx.message.channel.id] = {message.id: [True, clan_names]}
                except KeyError:
                    servers[ctx.message.guild.id] = {ctx.message.channel.id: {message.id: [True, clan_names]}}

            await set_json("servers.json", servers)
            client.loop.create_task(update(ctx.message.guild.id, ctx.message.channel.id, message.id)) \
                .set_name("Update{}".format(message))
        else:
            await ctx.send("Sorry, but you must input a clan name to be tracked!", delete_after=5)


    @bot.command()
    @has_permissions(manage_messages=True)
    async def pause(ctx):
        """Pauses the bot tracking in the current channel, if you have the right."""
        global servers

        await ctx.message.delete()
        await ctx.send("Pausing tracking in channel...", delete_after=2)

        try:
            for message in servers[ctx.message.guild.id][ctx.message.channel.id]:
                servers[ctx.message.guild.id][ctx.message.channel.id][message][0] = False
        except KeyError:
            await ctx.send("Sorry, but it looks like there aren't any clans currently being tracked in this channel!",
                           delete_after=5)

        await set_json("servers.json", servers)


    @bot.command()
    @has_permissions(manage_messages=True)
    async def resume(ctx):
        """Resumes tracking in the current channel, if you have the right."""
        global servers

        await ctx.message.delete()
        await ctx.send("Starting tracking in channel...", delete_after=2)

        try:
            for message in servers[ctx.message.guild.id][ctx.message.channel.id]:
                servers[ctx.message.guild.id][ctx.message.channel.id][message][0] = True
                client.loop.create_task(update(ctx.message.guild.id, ctx.message.channel.id, message))
        except KeyError:
            await ctx.send("Sorry, but it looks like there aren't any clans currently being tracked in this channel!",
                           delete_after=5)

        await set_json("servers.json", servers)


    @bot.command()
    @has_permissions(manage_messages=True)
    async def wipe(ctx):
        """Stops the bot tracking in the current channel, if you have the right."""
        global servers

        await ctx.message.delete()
        await ctx.send("Stopping tracking in channel...", delete_after=2)

        try:
            for message in servers[ctx.message.guild.id][ctx.message.channel.id]:
                del(servers[ctx.message.guild.id][ctx.message.channel.id])
        except KeyError:
            await ctx.send("Sorry, but it looks like there aren't any clans currently being tracked in this channel!",
                           delete_after=5)

        await set_json("servers.json", servers)


    @bot.command()
    async def lobby(ctx, name):
        """Returns a list of players in whatever server the named player is in"""
        name_embed = discord.Embed(title="Finding player {}".format(name))

        message = await ctx.send(embed=name_embed)

        cont = True
        current_name = []

        try:
            current_name = await dash.get_server_player_by_name(session, name)
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
                    tag_players += "{} {} {}\n".format(emojis[player.team], player.tag, player.name)
                    levels.append(player.level)
                for player in server.players:
                    if player not in players:
                        non_tag_players += "{} {} {}\n".format(emojis[player.team], player.tag, player.name)
                        levels.append(player.level)
                average = round(sum(levels) / len(levels))
                if server.password:
                    password = ":lock:"
                else:
                    password = ":unlock:"
                name_embed.add_field(
                    name="{} [{}/10] Average Level: {}\nCurrently playing: {}\n"
                         "Pass: {}".format(server.name, len(server.players), average, server.mode, password),
                    value="***{0}*** {1}".format(tag_players, non_tag_players))

            name_embed.set_footer(text="Bot made by RaspiBox. Made possible thanks to Zed's API.\nTime of "
                                       "update: {0} UTC".format(str(datetime.datetime.now(timezone.utc))[:-13]))

            await message.edit(embed=name_embed)
        else:
            name_embed.add_field(name="Unable to get data from Zed's API!", value="Please contact RaspiBox for "
                                                                                  "assistance.")
            await message.edit(embed=name_embed)


    @bot.command()
    @commands.dm_only()
    async def add_friend(ctx, *names):
        """Adds a friend to your friends notification list."""
        await ctx.send("Adding {} to your friends list!\nUse !friends to see your updated friends list.".format(names),
                       delete_after=5)
        try:
            for name in names:
                print(name)
                if name not in friends_list[ctx.author.id]:
                    friends_list[ctx.author.id].append(name)
        except KeyError:
            friends_list[ctx.author.id] = [name]

        if len(friends_list[ctx.author.id]) < 2:
            client.loop.create_task(friends_update(ctx.author.id))
        await set_json("friends.json", friends_list)


    @bot.command()
    @commands.dm_only()
    async def del_friend(ctx, name):
        """Removes a friend to your friends notification list."""
        await ctx.send(
            "Removing {} from your friends list!\nUse !friends to see your updated friends list.".format(name)
            , delete_after=5)
        friends_list[ctx.author.id].remove(name)
        await set_json("friends.json", friends_list)


    @bot.command()
    @commands.dm_only()
    async def wipe_friends(ctx, confirm=None):
        """Wipes all friends from your friends notification list."""
        if not confirm:
            await ctx.send("Using this command will wipe your friends list!\nAre you sure you wish to continue?")
            await ctx.send("To confirm, resend command with 'yes' after the command. E.G: !wipe_friends yes ")
        elif confirm.lower() == "yes":
            await ctx.send("Confirmed... Wiping friends list!")
            friends_list[ctx.author.id] = []

        await set_json("friends.json", friends_list)


    @bot.command()
    @commands.dm_only()
    async def friends(ctx):
        """Shows your friends notification list."""
        try:
            len(friends_list[ctx.author.id])
        except KeyError:
            await ctx.send("You currently don't have any friends! Use !add_friend [name] to add some.")
        if len(friends_list[ctx.author.id]) > 0:
            message = await ctx.send("Please wait...")
            friend_embed = discord.Embed(title="Friends:", colour=discord.Colour.gold())
            online_servers = []
            online_players = []

            for friend in friends_list[ctx.author.id]:
                current = await dash.get_server_player_by_name(session, friend)
                for server in current:
                    online_servers.append(server)
                    for player in server.players:
                        if friend.lower() in player.name.lower():
                            online_players.append(friend.lower())

            for server in online_servers:
                online_servers.remove(server)
                friends_string = ""
                levels = []
                if server.password:
                    password = ":lock:"
                else:
                    password = ":unlock:"
                for player in server.players:
                    levels.append(player.level)
                    for friend in friends_list[ctx.author.id]:
                        if friend.lower() in player.name.lower():
                            friends_string += "{} {} {}\n".format(emojis[player.team], player.tag, player.name)
                average = round(sum(levels) / len(server.players))
                friend_embed.add_field(name="{} [{}/10] Average Level: {}\nCurrently playing: {}\n"
                                            "Pass: {}".format(server.name, len(server.players), average, server.mode,
                                                              password),
                                       value=friends_string)

            for friend in friends_list[ctx.author.id]:
                if friend.lower() not in online_players:
                    friend_embed.add_field(name="*{}*".format(friend), value="{} is currently offline.".format(friend), inline=False)

            await message.edit(content="", embed=friend_embed)
        else:
            await ctx.send("You currently don't have any friends! Use !add_friend [name] to add some.")


    @bot.command()
    @commands.dm_only()
    async def mute(ctx, hours: float):
        """Mutes the friend notifications for the number of hours provided!"""
        global mute_list
        await ctx.send("Muting friends notifications for {} hours!".format(hours))
        mute_list[ctx.author.id] = hours*3600
        print(mute_list[ctx.author.id])


    @bot.command()
    @commands.dm_only()
    async def quiet(ctx, *hours):
        """Mutes the friend notifications throughout the specific quiet hours."""
        pass


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
    async def server_links(ctx):
        """Links to other cool servers!"""
        server_embed = discord.Embed(title="Recommended Servers: ",
                                     description="Have a look at these places for Hyper Dash content.")
        server_embed.add_field(name="DARK:", value="https://discord.gg/3kUGE7NWnj", inline=False)
        server_embed.add_field(name="VGAN:", value="https://discord.gg/bkzRYw58U2", inline=False)
        await ctx.send(embed=server_embed)


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
            await set_json("friends.json", {})
            await ctx.send("Resetting entire bot logs!", delete_after=2)
            await ctx.message.delete()
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def resume_all(ctx):
        """Resumes tracking in the every channel the bot is in, in every server, if you have the right."""
        if ctx.author.id == 344911466195058699 and not isinstance(ctx.channel, discord.DMChannel):
            global servers

            await ctx.message.delete()
            await ctx.send("Resuming all tracking...", delete_after=2)

            try:
                for server in servers:
                    for channel in servers[server]:
                        for message in servers[server][channel]:
                            if servers[server][channel][message][0]:
                                await update(ctx.message.guild.id, ctx.message.channel.id, message)
            except KeyError:
                await ctx.send("Error - some messages could not be found!")

            await set_json("servers.json", servers)
        else:
            await ctx.send("Sorry, but you don't have the privileges to do that!")


    @bot.command()
    async def uwu(ctx):
        await ctx.send("Hello Yellow, you're the only person that would use this surely!")


    @run.error
    @pause.error
    @wipe.error
    @resume.error
    @lobby.error
    @add_friend.error
    @del_friend.error
    @wipe_friends.error
    @friends.error
    @mute.error
    @optout.error
    @optin.error
    @ping.error
    async def permission_error(ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("Sorry, but you do not have the permissions to do that.", delete_after=5)
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("You have neglected to add in an argument after the command. Please use !help.",
                           delete_after=5)
        if isinstance(error, PrivateMessageOnly):
            await ctx.send("Sorry, this command can be used in DMs only. Please use !help.",
                           delete_after=5)


    bot.run(token)
