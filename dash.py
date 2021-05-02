import requests

rawList = ""


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


def update():
    global rawList
    try:
        rawList = requests.get("https://api.dashlist.info/fetch").json()
        return True
    except:
        return False


def get_servers():
    update()
    servers = []
    try:
        for server in rawList:
            name = str(server)
            region = rawList[server]['region']
            zone = rawList[server]['zone']
            version = rawList[server]['version']
            mode = rawList[server]['mode']
            password = rawList[server]['password']
            mutators = []
            players = []
            spectators = []
            levelLock = {}

            if 'mutators' in server:
                mutators = rawList[server]['mutators']

            if 'players' in rawList[server]:
                for player in rawList[server]['players']:
                    players.append(Player(player['name'], player['tag'], player['level'], player['team']))

            if 'spectators' in rawList[server]:
                for spectator in rawList[server]['spectators']:
                    spectators.append(Spectator(spectator['name'], spectator['tag']))

            if 'levelLock' in rawList[server]:
                levelLock = rawList[server]['levelLock']

            servers.append(Server(name, region, zone, version, mode, password, players, spectators, mutators, levelLock))

        return servers
    except KeyError:
        raise KeyError


def get_server_player_by_tag(tags):
    update()
    _tags = []
    for tag in tags:
        _tags.append(tag.lower())
    servers = get_servers()
    current = {}
    for server in servers:
        for player in server.players:
            if player.tag.lower() in _tags:
                try:
                    current[server] = current[server] + [player]
                except KeyError:
                    current[server] = [player]
            for tag in _tags:
                if tag in player.name.lower()[3:] or tag in player.name.lower()[:-3]:
                    try:
                        current[server] = current[server] + [player]
                    except KeyError:
                        current[server] = [player]
            try:
                flag = False
                for player in current[server]:
                    if player == player.name:
                        flag = True
                        if flag:
                            current[server].remove(player)
            except KeyError:
                pass
    return current


def get_server_player_by_name(name):
    update()
    name = name.lower()
    servers = get_servers()
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
    if update():
        print("\nCurrent list can be force updated using the update() routine. Returns True if successful, and False if "
              "not.\n")
        print("Current raw list can be accessed using the rawList variable\n    {}\n".format(rawList))

        print("Current players with a specific tag can be accessed using the get_server_player_by_tag() routine:")
        tags = "bb", "dark", "wrth", "obey", "hh"
        current_tags = get_server_player_by_tag(tags)
        for server in current_tags:
            levels = []
            players = current_tags[server]
            print(server.name)
            for player in players:
                print("        "+player.tag+" "+player.name)
                levels.append(player.level)
            for player in server.players:
                if player not in players:
                    print("    "+player.tag+" "+player.name)
                    levels.append(player.level)
            average = sum(levels)/len(levels)
            print("Average level: {}".format(average))

        print("\nCurrent players with a specific name can be accessed using the get_server_player_by_name() routine:")

        current_name = get_server_player_by_name("raspibox")
        for server in current_name:
            levels = []
            players = current_name[server]
            print(server.name)
            for player in players:
                print("        "+player.tag+" "+player.name)
                levels.append(player.level)
            for player in server.players:
                if player not in players:
                    print("    "+player.tag+" "+player.name)
                    levels.append(player.level)
            average = sum(levels)/len(levels)
            print("Average level: {}".format(average))
            print("\n")
    else:
        print("API Unavailable")
