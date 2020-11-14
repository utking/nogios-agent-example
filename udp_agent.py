from agent_helpers.generic_agent import GenericAgent
import requests
import json
import socket


class UdpAgent(GenericAgent):

    def __init__(self, bind_ip=None, bind_port=None, server_check_endpoint=None):
        super().__init__(bind_ip=bind_ip, bind_port=bind_port)
        self.server_check_endpoint = server_check_endpoint

        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_ip, self.bind_port))
        while True:
            data, addr = self.sock.recvfrom(self.BUFFER_SIZE)
            try:
                command_object = self.load_json(data)
                self.process_cmd(command_object)
            except json.JSONDecodeError:
                print('Could not parse {}', data.decode())
                continue

    def send_response(self, data: dict):
        resp = requests.post(self.server_check_endpoint, data=data)
        print(resp.text)

    def catch(self, signum, frame):
        print("{} received. Terminating".format(signum))
        if self.sock is not None:
            self.sock.close()
        self.exit(0)


if __name__ == '__main__':
    UdpAgent(bind_ip='0.0.0.0', bind_port=1811, server_check_endpoint='http://localhost:8000/services/status').start()
