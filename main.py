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
import user_pb2
import user_pb2_grpc
import sql_pb2
import sql_pb2_grpc


name: str = 'USER'
v: str = 'v2'

env_json_file: str = os.path.abspath('./env.json')

lingo = None
log = None

env = {}
env_list: List[str] = [
    'PORT',
    'HTTP_PORT',
    'HTTP_IP',
    'SQL_PORT',
    'SQL_IP'
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
    user_pb2_grpc.add_PingServicer_to_server(Server(), server)
    port = get('PORT')
    server.add_insecure_port(f'localhost:{port}')

    server.start()
    log.info('Started server at %s', port)
    server.wait_for_termination()

    log.info('Ending server')


def init_json() -> None:
    global env

    try:
        json_file = open(env_json_file, 'r')
        env = json.load(json_file)
    except FileNotFoundError as fe:
        log.warning('Did not find env json file - using env vars')


class Server(user_pb2_grpc.PingServicer):
    @staticmethod
    def get_user() -> str:
        ip: str = get('SQL_IP')
        port: str = get('SQL_PORT')
        addr: str = f'{ip}:{port}'

        log.info('Connecting to SQL service at %s', addr)
        channel = grpc.insecure_channel(addr)
        stub = sql_pb2_grpc.SQLStub(channel)

        response = stub.GetUser(sql_pb2.Ack(msg=True))
        user: str = response.name

        log.info('Got user %s', user)
        return user

    @staticmethod
    def get_friends(name: str) -> List[str]:
        friends: List[str] = []

        ip: str = get('HTTP_IP')
        port: str = get('HTTP_PORT')
        addr: str = f'{ip}:{port}'

        log.info('Connecting to HTTP service at %s', addr)
        channel = grpc.insecure_channel(addr)
        stub = http_pb2_grpc.DuoStub(channel)

        response = stub.GetFriends(http_pb2.User(name=name))
        friends = response.names

        return friends

    @staticmethod
    def send_users(names: List[str]) -> bool:
        ip: str = get('SQL_IP')
        port: str = get('SQL_PORT')
        addr: str = f'{ip}:{port}'

        log.info('Connecting to SQL service at %s', addr)
        channel = grpc.insecure_channel(addr)
        stub = sql_pb2_grpc.SQLStub(channel)

        response = stub.WriteUsers(sql_pb2.Users(names=names))
        return response.msg

    def Trigger(self, request, context):
        log.info('Received trigger from clock')
        name: str = Server.get_user()

        friends: List[str] = Server.get_friends(name)
        log.info('Found friends for "%s":', name)
        log.info(friends)
        log.info('Sending friends to be written')
        ack: bool = Server.send_users(friends)

        return user_pb2.Ack(msg=ack)


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
