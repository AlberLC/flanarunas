import asyncio
from collections.abc import Iterable

import psutil


def find_auth_key(args: Iterable[str]) -> str:
    for arg in args:
        if '--remoting-auth-token' in arg:
            return arg.split('=')[1]


def find_port(args: Iterable[str]) -> str:
    for arg in args:
        if '--app-port' in arg:
            return arg.split('=')[1]


def return_process(process_name: list[str]) -> psutil.Process | None:
    for process in psutil.process_iter():
        if process.name() in process_name:
            return process
    return None


async def return_ux_process_when_available() -> psutil.Process:
    process = None
    while not process:
        process = return_process(['LeagueClientUx.exe', 'LeagueClientUx'])
        await asyncio.sleep(0.5)
    return process
