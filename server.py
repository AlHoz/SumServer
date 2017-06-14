import uuid

import tornado.escape
import tornado.web
import tornado.websocket
from tornado.ioloop import IOLoop
from tornado.queues import Queue


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
                    IOLoop.current().spawn_callback(OnNewNumUpdate, num)
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


q = Queue()


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        Storage.clients.append(self)

    def on_close(self):
        Storage.clients.remove(self)


async def watch_queue():
    while True:
        num = await q.get()
        Storage.sum += num

        for client in Storage.clients:
            client.write_message({"sum": Storage.sum})


async def OnNewNumUpdate(num):
    await q.put(num)


def make_app():
    return tornado.web.Application([
        (r"/session", SessionHandler),
        (r"/vote", VoteHandler),
        (r"/online", WSHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8080, address='127.0.0.1')
    IOLoop.instance().add_callback(watch_queue)
    IOLoop.current().start()
