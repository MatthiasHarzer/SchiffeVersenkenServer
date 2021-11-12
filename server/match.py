import random

from client import Client
from util import uniqueRandomString


class Match:
    def __init__(self, player0: Client, server):
        self.id = None
        self.id = uniqueRandomString([m.id for m in ongoing_matches], 5).upper()
        self.host = player0
        self.players: list[Client] = [
            player0
        ]
        self.settings = {
            # DEFAULT SETTINGS
        }
        self.stats = {
            player0: {
                "ships": [],
                "bombed": []
            }
        }

        self.currentPlayer = None

        from main import Server
        self.server: Server = server

        self.running = False

        ongoing_matches.append(self)

    # Add Player to match
    def __addPlayer(self, player: Client) -> (str,):
        if len(self.players) <= 1:
            self.players.append(player)
            self.stats[player] = {
                "ships": [],
                "bombed": []
            }
            return "SUCCESS", self
        else:
            return "FULL", None

    # Start placing phase
    def __startPlace(self):
        self.broadcast({
            "type": "GAME_STATE",
            "state": "PLACE"
        })

    # Start bombing phase
    def __startBomb(self):
        self.running = True
        self.currentPlayer = self.players[round(random.random() * len(self.players) - 1)]
        self.__sendGameRunningUpdate()

    # Send update about current turn
    def __sendGameRunningUpdate(self):
        self.broadcast({
            "type": "GAME_STATE",
            "state": f"P{self.players.index(self.currentPlayer)}"
        })

    def __checkVictory(self):
        for player, stats in self.stats.items():
            print(player, stats)
            lost = True
            for ship in stats.get("ships", []):
                for ship_part in ship:
                    if ship_part not in stats.get("bombed", []):
                        lost = False
            if lost:
                self.broadcast({
                    "type": "GAME_STATE",
                    "state": f"W{len(self.players) - 1 - self.players.index(player)}"
                })
                break

    # Bomb a field of a player
    def __bomb(self, field: list[int], map_player: Client):
        self.stats[map_player]["bombed"].append(field)
        self.__sendFieldResp(field, self.players.index(map_player),
                             "HIT" if field in self.stats[map_player]["ships"] else "MISS")

    # Send a field response to all players
    def __sendFieldResp(self, field: list[int], map_player_num: int, state: str):
        self.broadcast({
            "type": "FIELD_RESP",
            "field": field,
            "map": map_player_num,
            "state": state
        })

    def __removePlayer(self, player: Client):
        self.players.remove(player)
        self.stats.pop(player)

    # Switch active player
    def cyclePlayer(self):

        self.currentPlayer = self.players[len(self.players) - 1 - self.players.index(self.currentPlayer)]

    # Request bombing a field
    def fieldReq(self, field: list[int], player: Client):
        if player == self.currentPlayer and player in self.players:
            field_player = self.players[len(self.players) - 1 - self.players.index(player)]
            if field not in self.stats[field_player]["bombed"]:
                self.__bomb(field, field_player)
                self.cyclePlayer()
                self.__sendGameRunningUpdate()
                self.__checkVictory()
            else:
                self.broadcast({
                    "type": "FIELD_RESP",
                    "field": field,
                    "state": "FCKU"
                })

    # Set ships
    def setMap(self, player: Client, ships: list[list[list[int]]]):
        if player in self.players and not self.running:
            self.stats[player]["ships"] = ships

        all_set = True
        for p, data in self.stats.items():
            if len(data.get("ships", [])) <= 0:
                all_set = False
                break
        if all_set:
            self.__startBomb()

    def setSettings(self, player: Client, settings: dict):
        if player is self.host:
            self.settings = settings
            self.broadcast({
                "type": "SETTINGS",
                "settings": self.settings
            })

    # Start the placing phase (only host)
    def requestStartPlacing(self, player: Client):
        if self.host == player:
            self.__startPlace()

    # Send login update when new palyer joins match
    def sendPlayerUpdate(self):
        self.broadcast({
            "type": "SETTINGS",
            "settings": self.settings
        })
        for player in self.players:
            self.server.send(player, {
                "type": "LOGIN",
                "name": player.name,
                "player": [p.name for p in self.players],
                "playerNr": self.players.index(player),
            })

    # Boradcast a message to match players
    def broadcast(self, data: dict):
        for player in self.players:
            self.server.send(player, data)

    # Try joining a match
    @staticmethod
    def joinById(id_: str, player: Client) -> (bool, str):
        for m in ongoing_matches:
            if m.id == id_:
                return m.__addPlayer(player)
        return "NOT_FOUND", None

    # get the match, depending on which players are connected
    @staticmethod
    def getByPlayer(player: Client):
        for m in ongoing_matches:
            if player in m.players:
                return m
        return None

    # Remove a player from all matches (when disconnect); if host -> delete match
    @staticmethod
    def removePlayer(player: Client):
        for match in ongoing_matches:
            if player in match.players:
                if match.host == player:
                    ongoing_matches.remove(match)
                else:
                    match.__removePlayer(player)
                    # m.players.remove(player)


ongoing_matches: list[Match] = []
