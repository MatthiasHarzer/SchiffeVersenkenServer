import random

from server.client import Client
from server.util import uniqueRandomString


class Match:
    def __init__(self, player0: Client, server):
        self.id = None
        self.id = uniqueRandomString([m.id for m in ongoing_matches], 5).upper()
        self.host = player0
        self.players: list[Client] = [
            player0
        ]
        self.settings = {

        }
        self.stats = {
            player0: {
                "ships": [],
                "bombs": []
            }
        }

        self.currentPlayer = None

        from server.main import Server
        self.server: Server = server

        self.running = False

        ongoing_matches.append(self)

    def __addPlayer(self, player: Client) -> (str,):
        if len(self.players) <= 1:
            self.players.append(player)
            self.stats[player] = {
                "ships": [],
                "bombs": []
            }
            return "SUCCESS", self
        else:
            return "FULL", None

    def __startPlace(self):
        self.broadcast({
            "type": "GAME_STATE",
            "state": "PLACE"
        })

    def __startBomb(self):
        self.running = True
        self.currentPlayer = self.players[round(random.random() * len(self.players) - 1)]
        self.__sendGameRunningUpdate()

    def __sendGameRunningUpdate(self):
        self.broadcast({
            "type": "GAME_STATE",
            "state": f"P{self.players.index(self.currentPlayer)}"
        })

    def __bomb(self, field: list[int], map_player: Client):
        self.__sendFieldResp(field, self.players.index(map_player), "HIT" if field in self.stats[map_player]["ships"] else "MISS")

    def __sendFieldResp(self, field: list[int], map_player_num: int, state: str):
        self.broadcast({
            "field": field,
            "map": map_player_num,
            "state": state
        })

    def cyclePlayer(self):
        self.currentPlayer = self.players[len(self.players)-1-self.players.index(self.currentPlayer)]

    def fieldReq(self, field: list[int], player: Client):
        if player == self.currentPlayer and player in self.players:
            self.__bomb(field, self.players[len(self.players)-1-self.players.index(player)])
            self.cyclePlayer()
            self.__sendGameRunningUpdate()

    def setMap(self, player: Client, ships: list):
        if player in self.players:
            self.stats[player]["ships"] = ships

        all_set = True
        for p, data in self.stats.items():
            if len(data.get("ships", [])) <= 0:
                all_set = False
                break
        if all_set:
            self.__startBomb()

    def requestStartPlacing(self, player: Client):
        if self.players.index(player) == 0:
            self.__startPlace()

    def broadcast(self, data: dict):
        for player in self.players:
            self.server.send(player, data)

    @staticmethod
    def joinById(id_: str, player: Client) -> (bool, str):
        for m in ongoing_matches:
            if m.id == id_:
                return m.__addPlayer(player)
        return "NOT_FOUND", None

    @staticmethod
    def getByPlayer(player: Client):
        for m in ongoing_matches:
            if player in m.players:
                return m
        return None

    @staticmethod
    def removePlayer(player: Client):
        for m in ongoing_matches:
            if player in m.players:
                if m.host == player:
                    ongoing_matches.remove(m)
                else:
                    m.players.remove(player)


ongoing_matches: list[Match] = []
