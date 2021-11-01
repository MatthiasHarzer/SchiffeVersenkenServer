import json

from websocket_server import WebsocketServer

from client import Client
from server.match import Match
from server.util import genericName

DEFAULT_PORT = 8080
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

        Match.removePlayer(Client.getByID(client.get("id", -1)))
        Client.remove(client)

    def on_message(self, c, _, message):
        try:
            client = Client.getOrCreate(c)

            match = Match.getByPlayer(client)

            data: dict = json.loads(message)

            print(f"RECEIVED: {data}")

            match data.get("type", None):
                case "LOGIN":
                    name = data.get("name", "")
                    if len(name) <= 0:
                        name = genericName()
                    client.name = name

                    self.send(client, {
                        "type": "LOGIN",
                        "name": name
                    })

                case "CREATE":
                    match = Match(client, self)

                    self.send(client, {
                        "type": "CREATE",
                        "id": match.id
                    })

                case "JOIN":
                    id_ = data.get("id", "")
                    state, match = Match.joinById(id_, client)
                    self.send(client, {
                        "type": "JOIN",
                        "state": state
                    })
                    if match:
                        self.sendLoginUpdate(match.players)

                case "GAME_STATE":
                    state = data.get("state", "")
                    match state:
                        case "PLACE":
                            if match:
                                match.requestStartPlacing(client)

                case "SET_MAP":
                    ships = data.get("map", [])

                    if match and len(ships > 0):
                        match.setMap(client, ships)

                case "FIELD_REQ":
                    field = data.get("field", [])

                    if match and len(field == 2):
                        match.setMap(client, ships)


        except Exception as e:
            print(f"error {e}")

    def send(self, client: Client, data: dict):
        print(f"SENDING: {data} to {client}")
        self.send_message(client.client, json.dumps(data))

    # Send login update when new palyer joins match
    def sendLoginUpdate(self, clients: list[Client]):
        for c in clients:
            match = Match.getByPlayer(c)
            self.send(c, {
                "type": "LOGIN",
                "name": c.name,
                "player": [p.name for p in match.players] if match else [],
                "playerNr": match.players.index(c) if match else -1,
            })

if __name__ == "__main__":
    s = Server()
