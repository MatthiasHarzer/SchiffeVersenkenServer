class Client:
    clients: list = []

    def __init__(self, client):
        self.client = client
        self.id = client.get("id")
        self.handler = client.get("handler")
        self.address = client.get("address")
        self.name = ""
        self.playerNum = -1

        Client.clients.append(self)

    def __str__(self):
        return f"Client {self.id} \"{self.name}\" @ {self.address} "

    @staticmethod
    def getOrCreate(client):
        for c in Client.clients:
            if c.id == client.get("id", -1):
                return c
        else:
            return Client(client)

    @staticmethod
    def remove(client):
        Client.clients.remove([c for c in Client.clients if c.id == client.get("id", -1)][0])


    @staticmethod
    def getByID(id_: int):
        c = [cc for cc in Client.clients if cc.id == id_]
        if len(c):
            return c[0]
        else:
            return None
