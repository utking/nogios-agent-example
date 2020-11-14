import socket
import json
from subprocess import Popen, PIPE
import shlex
import signal
import sys


class GenericAgent(object):
    BUFFER_SIZE = 1024

    STATUS_MAP = {
        0: 'OK',
        1: 'WARNING',
        2: 'CRITICAL',
        3: 'UNKNOWN',
        4: 'BLOCKER',
    }

    def __init__(self, bind_ip=None, bind_port=None):
        if bind_ip is None or bind_port is None:
            raise Exception('Bind address and port must be specified')

        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.__setup()

    def __setup(self):
        signal.signal(signal.SIGTERM, self.catch)
        signal.signal(signal.SIGINT, self.catch)
        signal.siginterrupt(signal.SIGTERM, False)

    def catch(self, signum, frame):
        print("{} received. Must cleanup before exit".format(signum))
        self.exit(1)

    def exit(self, code):
        sys.exit(code)

    @staticmethod
    def __get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    @staticmethod
    def parse_commands(raw_cmd: str):
        return raw_cmd.strip()

    @staticmethod
    def load_json(data: bytes):
        return json.loads(data.decode())

    @staticmethod
    def dump_json(data: dict):
        return json.dumps(data)

    def process_cmd(self, command_object: dict):
        cmd = command_object.get('cmd')
        host_name = command_object.get('host_name')
        service_name = command_object.get('service_name')

        if cmd is None or not isinstance(cmd, str) or cmd.strip() == '':
            print('No command to execute')
            return None
        if host_name is None or not isinstance(host_name, str) or host_name.strip() == '':
            print('Unknown hostname')
            return None

        args = command_object.get('args')
        if not isinstance(args, list):
            args = []

        host_name = host_name.strip()
        command = self.parse_commands(cmd.strip() + ' ' + ' '.join(list(map(lambda x: str(x), args))))
        if command is not None and isinstance(command, str):
            ret_code, stdout, stderr = self.execute_command(command)
            print('ret_code', ret_code)
            status = self.STATUS_MAP.get(ret_code)
            if status is None:
                status = 'WARNING'
            if len(stdout) > 0:
                for line in stdout:
                    print(line)
            if len(stderr) > 0 and stderr != ['']:
                status = 'CRITICAL'
                print('STDERR:')
                for line in stderr:
                    print(line)
            print('=' * 20)

            self.send_response({
                'host_name': host_name,
                'name': service_name,
                # 'address': self.__get_ip(),
                'status_code': status,
                'ret_code': ret_code,
                'output': '{}{}'.format('\n'.join(stdout), '\n'.join(stderr)),
            })

    @staticmethod
    def execute_command(raw_cmd: str):
        commands = raw_cmd.split('|')
        stdin = None
        prev_cmd = None
        if len(commands) > 0:
            for command_line in commands:
                command_array = shlex.split(command_line)
                if stdin is None:
                    ret = Popen(command_array, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                else:
                    ret = Popen(command_array, stdin=stdin, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                    prev_cmd.stdout.close()
                stdin = ret.stdout
                prev_cmd = ret

            cmd_stdout, cmd_stderr = ret.communicate()
            code = ret.returncode
            return code, cmd_stdout.split('\n'), cmd_stderr.split('\n')
        return -1, [], []

    def start(self):
        print('Generic Agent cannot be used for processing checks')

    def send_response(self, data: dict):
        print('Generic Agent cannot be used for processing checks')


if __name__ == '__main__':
    GenericAgent(bind_ip='127.0.0.1', bind_port=1811).start()
