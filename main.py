import atexit
import grpc
import json
import logging
import os

from concurrent import futures
from typing import Dict
from typing import List
from typing import Tuple


import http_pb2
import http_pb2_grpc


name: str = 'HTTP'
v: str = 'v2'

env_json_file: str = os.path.abspath('./env.json')

lingo = None
log = None

env = {}
env_list: List[str] = [
    'PORT',
    'HTTP_PORT'
]


def get(key: str) -> str:
    global env
    return env[key]


def init_env() -> None:
    for e in env_list:
        if e in env:
            msg: str = 'Found env var "%s" in file with default value "%s"'
            log.info(msg, e, get(e))
        else:
            env[e] = os.environ[e]
            log.info('Found env var "%s" with value "%s"', e, env[e])


def init_log() -> None:
    global log
    global name
    global v

    logging.basicConfig(
        format=f'[{v}] {name} %(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

    log = logging.getLogger(name)
    log.info('hi')


def init_atexit() -> None:
    def end():
        logging.info('bye')

    atexit.register(end)


def init_log() -> None:
    global log
    global name
    global v

    logging.basicConfig(
        format=f'[{v}] [{name}] %(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

    log = logging.getLogger(name)
    log.info('hi')


def init_server() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    http_pb2_grpc.add_DuoServicer_to_server(Server(), server)
    port = get('PORT')
    server.add_insecure_port(f'localhost:{port}')

    server.start()
    logging.info('Started server at %s', port)
    server.wait_for_termination()

    logging.info('Ending server')


def init_json() -> None:
    global env

    try:
        json_file = open(env_json_file, 'r')
        env = json.load(json_file)
    except FileNotFoundError as fe:
        log.warning('Did not find env json file - using env vars')


def get_friends(tup: Tuple[int, str]) -> List[Tuple[int, str]]:
    global lingo

    name: str = tup[1]
    log.info('Querying friends for %s', tup)

    lingo.set_username(name)

    friends_resp = lingo.get_friends()
    friends: List[Tuple[int, str]] = []

    for fob in friends_resp:
        user: str = fob['username']
        idd: int = fob['id']
        tup: Tuple[int, str] = (idd, user)
        log.info('Found friend %d, %s for %s', idd, user, name)

        friends.append(tup)

    log.info('Found friends %d friends for %s', len(friends), name)
    return friends


class Server(http_pb2_grpc.DuoServicer):
    @staticmethod
    def get_http_request(name: str) -> List[str]:
        lingo.set_username(name)
        friends_resp = lingo.get_friends()
        friends: List[str] = []

        for fob in friends_resp:
            fob: str = fob['username']
            friends.append(fob)

        return friends

    def GetFriends(self, request, context):
        name: str = request.name
        logging.info('Received username %s', name)

        friends: List[str] = Server.get_http_request(name)
        logging.info('Found friends for "%s":', name)
        logging.info(friends)

        return http_pb2.Friends(names=friends)


def init() -> None:
    init_log()
    init_json()
    init_env()
    init_atexit()
    init_server()


def main() -> None:
    init()


if __name__ == '__main__':
    main()
