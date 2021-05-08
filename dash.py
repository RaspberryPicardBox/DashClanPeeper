import requests
import asyncio
import aiohttp


class Player:
    name = ""
    tag = ""
    level = ""
    team = ""

    def __init__(self, name, tag, level, team):
        self.name = name
        self.tag = tag
        self.level = level
        self.team = team


class Spectator:
    name = ""
    tag = ""

    def __init__(self, name, tag):
        self.name = name
        self.tag = tag


class Server:
    name = ""
    region = ""
    zone = ""
    version = ""
    mode = ""
    mutators = []
    password = False
    levelLock = {}

    players = []
    spectators = []

    def __init__(self, name, region, zone, version, mode, password, players=None, spectators=None, mutators=None,
                 levelLock=None):
        self.name = name
        self.region = region
        self.zone = zone
        self.version = version
        self.mode = mode
        if password == "False":
            self.password = False
        elif password == "True":
            self.password = True
        if players:
            self.players = players
        if spectators:
            self.spectators = spectators
        if mutators:
            self.mutators = mutators
        if levelLock:
            self.levelLock = levelLock


async def get_session():
    return aiohttp.ClientSession()


async def close_session(session):
    await session.close()


async def update(session):
    raw_list = []
    async with session.get("https://api.dashlist.info/fetch") as response:
        if response.status == 200:
            raw_list = await response.json()
            return raw_list
        else:
            return False


async def get_servers(session):
    raw_list = await update(session)
    if not raw_list:
        raise KeyError
    servers = []
    try:
        for server in raw_list:
            name = str(server)
            region = raw_list[server]['region']
            zone = raw_list[server]['zone']
            version = raw_list[server]['version']
            mode = raw_list[server]['mode']
            password = raw_list[server]['password']
            mutators = []
            players = []
            spectators = []
            levelLock = {}

            if 'mutators' in server:
                mutators = raw_list[server]['mutators']

            if 'players' in raw_list[server]:
                for player in raw_list[server]['players']:
                    players.append(Player(player['name'], player['tag'], player['level'], player['team']))

            if 'spectators' in raw_list[server]:
                for spectator in raw_list[server]['spectators']:
                    spectators.append(Spectator(spectator['name'], spectator['tag']))

            if 'levelLock' in raw_list[server]:
                levelLock = raw_list[server]['levelLock']

            servers.append(Server(name, region, zone, version, mode, password, players, spectators, mutators, levelLock))

        return servers
    except KeyError:
        raise KeyError


async def get_server_player_by_tag(session, tags: list):
    raw_list = await update(session)
    if not raw_list:
        raise KeyError
    _tags = []
    for tag in tags:
        _tags.append(tag.lower())
    servers = await get_servers(session)
    current = {}
    for server in servers:
        for player in server.players:
            if player.tag.lower() in _tags and player.tag.lower() != "":
                try:
                    current[server] = current[server] + [player]
                except KeyError:
                    current[server] = [player]
            for tag in _tags:
                if tag in player.name.lower()[0:len(tag)] and player.name.lower()[len(tag):len(tag)+1] == " " or tag in player.name.lower()[-len(tag):len(player.name)] and player.name.lower()[-len(tag)-1:len(player.name)-2] == " ":
                    try:
                        current[server] = current[server] + [player]
                    except KeyError:
                        current[server] = [player]
    return current


async def get_server_player_by_name(session, name):
    raw_list = await update(session)
    if not raw_list:
        raise KeyError
    name = name.lower()
    servers = await get_servers(session)
    current = {}
    for server in servers:
        for player in server.players:
            if name in player.name.lower() and player.name.lower() != "":
                try:
                    current[server] = current[server] + [player]
                except KeyError:
                    current[server] = [player]
    return current


if __name__ == "__main__":
    async def main():
        session = await get_session()

        tags = ["dark", "zero", "bb", "fr", "uk"]

        servers = await get_server_player_by_tag(session, tags)

        print("\n-----CLANS-----\n")
        for server in servers:
            print(server.name)
            for player in server.players:
                if player.tag.lower() in tags:
                    print("    {} {}".format(player.tag, player.name))
                else:
                    print("{} {}".format(player.tag, player.name))
            print("\n")

        name = "Emzion"
        names = await get_server_player_by_name(session, name)

        print("\n-----NAME-----\n")
        for server in names:
            print(server.name)
            for player in server.players:
                if player.name != name:
                    print(player.name)
                else:
                    print("    ", player.name)

        await close_session(session)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
