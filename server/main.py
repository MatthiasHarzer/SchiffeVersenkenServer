import json

from websocket_server import WebsocketServer

from client import Client
from match import Match
from util import genericName

DEFAULT_PORT = 4269
DEFAULT_HOST = "0.0.0.0"


# client = {
#             'id': self.id_counter,
#             'handler': handler,
#             'address': handler.client_address
#         }

class Server(WebsocketServer):
    def __init__(self, threaded=False):
        super().__init__(DEFAULT_HOST, DEFAULT_PORT)

        # Register callbacks
        self.set_fn_new_client(self.on_connect)
        self.set_fn_client_left(self.on_disconnect)
        self.set_fn_message_received(self.on_message)

        print("STARTING SERVER")

        self.run_forever(threaded=threaded)

    def on_connect(self, client, _):
        print("CLIENT CONNECTED", client)
        Client.getOrCreate(client)

    def on_disconnect(self, client, _):
        print("CLIENT DISCONNECTED", client)
        c = Client.getByID(client.get("id", -1))
        match = Match.getByPlayer(c)

        Match.removePlayer(Client.getByID(client.get("id", -1)))
        Client.remove(client)
        if match:
            match.sendPlayerUpdate()

    def on_message(self, c, _, message):
        try:
            client = Client.getOrCreate(c)

            match = Match.getByPlayer(client)

            data: dict = json.loads(message)

            print(f"RECEIVED: {data}")

            match data.get("type", None):
                case "LOGIN":
                    name = data.get("name", "")
                    if not name or len(name) <= 0:
                        name = genericName()
                    client.name = name

                    self.send(client, {
                        "type": "LOGIN",
                        "name": name
                    })
                    if match:
                        match.sendPlayerUpdate()

                case "CREATE":
                    match = Match(client, self)
                    mid = data.get("mid", "")

                    self.send(client, {
                        "type": "CREATE",
                        "id": match.id,
                        "mid": mid
                    })
                    match.sendPlayerUpdate()

                    # for _ in range(50):
                    #     match.broadcast({
                    #         "type": "CHAT",
                    #         "message": "Test message",
                    #         "playerNr": match.players.index(client)
                    #     })
                    #
                    #
                    # match.broadcast({
                    #     "type": "CHAT",
                    #     "message": "Very long test message to test the test chat test applicatoin of the Schiffeversenken game yesssssssssss",
                    #     "playerNr": match.players.index(client)
                    # })

                case "JOIN":
                    id_ = data.get("id", "")
                    mid = data.get("mid", "")
                    state, match = Match.joinById(id_, client)
                    self.send(client, {
                        "type": "JOIN",
                        "state": state,
                        "mid": mid
                    })
                    if match:
                        match.sendPlayerUpdate()
                case "LEAVE":
                    Match.removePlayer(client)

                case "KICK":
                    player_nr = data.get("playerNr", -1)
                    if client == match.players[player_nr] or match.host == client:
                        Match.removePlayer(match.players[player_nr])

                case "GAME_STATE":
                    state = data.get("state", "")
                    match state:
                        case "PLACE":
                            if match:
                                match.requestStartPlacing(client)

                case "SET_MAP":
                    ships = data.get("map", [[[]]])

                    if match and len(ships) > 0:
                        match.setMap(client, ships)

                case "FIELD_REQ":
                    field = data.get("field", [])

                    if match and len(field) == 2:
                        match.fieldReq(field, client)

                case "SETTINGS":
                    settings = data.get("settings", [])
                    if match and len(settings) > 0:
                        match.setSettings(client, settings)

                case "CHAT":
                    message = data.get("message", None)
                    if match and message:
                        match.broadcast({
                            "type": "CHAT",
                            "message": message,
                            "playerNr": match.players.index(client)
                        })

        except Exception as e:
            print(f"error {e}")

    def send(self, client: Client, data: dict):
        print(f"SENDING: {data} to {client}")
        self.send_message(client.client, json.dumps(data))


if __name__ == "__main__":
    s = Server()
