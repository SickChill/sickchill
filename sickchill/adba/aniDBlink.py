import socket
import sys
import threading
import zlib
from time import sleep, time
from typing import Any, Dict

from .aniDBcommands import Command
from .aniDBerrors import AniDBBannedError, AniDBError, AniDBMustAuthError, AniDBPacketCorruptedError
from .aniDBresponses import ResponseResolver


class AniDBLink(threading.Thread):
    def __init__(self, server, port, myport, logFunction, delay=2, timeout=20, log_private=False):
        super().__init__()
        self.server = server
        self.port = port
        self.target = (server, port)
        self.timeout = timeout

        self.name = "ANIDB-LINK"

        self.myport = myport
        self.sock = None
        self.bound = self.connectSocket(myport, self.timeout)

        self.cmd_queue: Dict[Any, Command] = {None: None}
        self.resp_tagged_queue = {}
        self.resp_untagged_queue = []
        self.tags = []
        self.lastpacket = time()
        self.delay = delay
        self.session = None
        self.banned = False
        self.crypt = None

        self.log = logFunction
        self.log_private = log_private

        self._stop = threading.Event()
        self._quiting = False
        self.setDaemon(True)
        self.start()

    def connectSocket(self, myport, timeout):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        portlist = [myport] + [7654]
        for port in portlist:
            try:
                self.sock.bind(("", port))
            except Exception:
                continue
            else:
                self.myport = port
                return True
        else:
            return False

    def disconnectSocket(self):
        if self.sock:
            self.sock.close()

    def stop(self):
        self.log("Releasing socket and stopping link thread")
        self._quiting = True
        self.disconnectSocket()
        self._stop.set()

    def stopped(self):
        return self._stop.is_set()

    @staticmethod
    def print_log(data):
        print(data)

    def print_log_dummy(self, data):
        pass

    def run(self):
        while not self._quiting:
            try:
                data = self.sock.recv(8192)
            except socket.timeout:
                self._handle_timeouts()
                continue

            self.log("NetIO < %s" % repr(data))
            try:
                for i in range(2):
                    try:
                        tmp = data
                        resp = None
                        if tmp[:2] == b"\x00\x00":
                            self.log("Attempting inflation")
                            tmp = zlib.decompressobj().decompress(tmp[2:])
                            self.log("UnZip | %s" % repr(tmp))
                        self.log("Decoding")
                        tmp = tmp.decode("utf8")
                        self.log("Parsing")
                        resp = ResponseResolver(tmp)
                        self.log("Response success!")
                    except Exception:
                        self.log("ResponseResolver Error")
                        sys.excepthook(*sys.exc_info())
                        self.crypt = None
                        self.session = None
                    else:
                        break
                if not resp:
                    raise AniDBPacketCorruptedError("Either decrypting, decompressing or parsing the packet failed")
                cmd = self._cmd_dequeue(resp)
                resp = resp.resolve(cmd)
                resp.parse()
                if resp.rescode in ("200", "201"):
                    self.session = resp.attrs["sesskey"]
                if resp.rescode in ("209",):
                    print("sorry encryption is not supported")
                    raise Exception
                    # self.crypt=aes(md5(resp.req.apipassword+resp.attrs['salt']).digest())
                if resp.rescode in ("203", "403", "500", "501", "503", "506"):
                    self.session = None
                    self.crypt = None
                if resp.rescode in ("504", "555"):
                    self.banned = True
                    print("AniDB API informs that user or client is banned:", resp.resstr)
                resp.handle()
                if not cmd or not cmd.mode:
                    self._resp_queue(resp)
                else:
                    self.tags.remove(resp.restag)
            except Exception:
                self.log("Catastrophic error - Closing anidb thread")
                sys.excepthook(*sys.exc_info())
                print("Avoiding flood by paranoidly panicing: Aborting link thread, killing connection, releasing waiters and quiting")
                self.disconnectSocket()
                try:
                    cmd.waiter.release()
                except Exception:
                    pass

                for tag, cmd in self.cmd_queue.items():
                    try:
                        cmd.waiter.release()
                    except Exception:
                        pass

                sys.exit()

    def _handle_timeouts(self):
        willpop = []
        for tag, cmd in self.cmd_queue.items():
            if not tag:
                continue
            if time() - cmd.started > self.timeout:
                self.tags.remove(cmd.tag)
                willpop.append(cmd.tag)
                cmd.waiter.release()

        for tag in willpop:
            self.cmd_queue.pop(tag)

    def _resp_queue(self, response):
        if response.restag:
            self.resp_tagged_queue[response.restag] = response
        else:
            self.resp_untagged_queue.append(response)

    def getresponse(self, command):
        if command:
            resp = self.resp_tagged_queue.pop(command.tag)
        else:
            resp = self.resp_untagged_queue.pop()
        self.tags.remove(resp.restag)
        return resp

    def _cmd_queue(self, command):
        self.cmd_queue[command.tag] = command
        self.tags.append(command.tag)

    def _cmd_dequeue(self, resp) -> Command:
        if not resp.restag:
            return None
        else:
            return self.cmd_queue.pop(resp.restag)

    def _delay(self):
        return self.delay < 2.1 and 2.1 or self.delay

    def _do_delay(self):
        age = time() - self.lastpacket
        delay = self._delay()
        if age <= delay:
            sleep(delay - age)

    def _send(self, command):
        if self.banned:
            self.log("NetIO | BANNED")
            raise AniDBBannedError("Not sending, banned")
        self._do_delay()
        self.lastpacket = time()
        command.started = time()
        data = command.raw_data()

        encoded_data = data.encode("utf-8")

        self.sock.sendto(encoded_data, self.target)

        if command.command == "AUTH" and self.log_private:
            self.log("NetIO > sensitive data is not logged!")
        else:
            self.log("NetIO > %s" % repr(data))

    def new_tag(self):
        if not len(self.tags):
            maxtag = "T000"
        else:
            maxtag = max(self.tags)
        newtag = "T%03d" % (int(maxtag[1:]) + 1)
        return newtag

    def request(self, command):
        if not self.sock and self.connectSocket(self.myport, self.timeout):
            self.log("Not connected to aniDB, not sending command")
            raise AniDBError("No Socket")

        if not (self.session and command.session) and command.command not in ("AUTH", "PING", "ENCRYPT"):
            raise AniDBMustAuthError("You must be authed to execute commands besides AUTH and PING")
        command.started = time()
        self._cmd_queue(command)
        self._send(command)
