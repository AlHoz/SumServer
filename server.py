import uuid
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.websocket


class SessionHandler(tornado.web.RequestHandler):
    def post(self):

        while True:
            token = uuid.uuid4().hex
            if token not in Storage.tokens:
                Storage.tokens.add(token)
                break
        self.write({"token": token})


class VoteHandler(tornado.web.RequestHandler):
    def post(self):
        if self.request.headers.get("X-TOKEN") in Storage.tokens:
            data = tornado.escape.json_decode(self.request.body)
            if 'num' in data:
                try:
                    num = int(data["num"])
                    OnNewNumUpdate(num)
                except ValueError:
                    self.__error_response(400, "Unrecognizable request")
            else:
                self.__error_response(400, "Unrecognizable request")
        else:
            self.__error_response(403, "You're not authorized")

    def __error_response(self, status, message):
        self.set_status(status)
        self.write({"err": message})


class Storage:
    clients = []
    tokens = set()
    sum = 0


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        Storage.clients.append(self)

    def on_close(self):
        Storage.clients.remove(self)


def OnNewNumUpdate(num):
    Storage.sum += num
    for client in Storage.clients:
        client.write_message({"sum": Storage.sum})


def make_app():
    return tornado.web.Application([
        (r"/session", SessionHandler),
        (r"/vote", VoteHandler),
        (r"/online", WSHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8080, address='127.0.0.1')
    tornado.ioloop.IOLoop.current().start()
