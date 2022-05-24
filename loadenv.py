import os

def load_env():
    with open('.env') as env:
        for line in env.readlines():
            commands = line.split('=')
            os.environ[commands[0]] = commands[1]