from agent_helpers.generic_agent import GenericAgent
import json
import socket
import ssl


class TcpAgent(GenericAgent):

    def __init__(self, bind_ip=None, bind_port=None):
        super().__init__(bind_ip=bind_ip, bind_port=bind_port)

        self.sock = None
        self.conn = None
        self.SSL_CIPHER_FILTER = 'ALL:!DES:!RC4:!MD5:!PSK:!LOW:@SECLEVEL=0'

    def start(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_default_certs()
        context.set_ciphers(self.SSL_CIPHER_FILTER)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.bind_ip, self.bind_port))
            sock.listen(5)
            with context.wrap_socket(sock, server_side=True) as ssock:
                while True:
                    try:
                        self.conn, addr = ssock.accept()
                    except Exception as e:
                        print('SSL accept error {}'.format(e))
                        continue
                    print('Wait a new command')
                    data = self.conn.recv(self.BUFFER_SIZE)
                    if not data:
                        continue
                    try:
                        command_object = self.load_json(data)
                        self.process_cmd(command_object)
                    except json.JSONDecodeError:
                        print('Could not parse {}', data.decode())
                        continue

    def send_response(self, data: dict):
        if self.conn is not None:
            self.conn.send(self.dump_json(data).encode())

    def catch(self, signum, frame):
        print("{} received. Terminating".format(signum))
        if self.conn is not None:
            self.conn.close()
        self.exit(0)


if __name__ == '__main__':
    TcpAgent(bind_ip='0.0.0.0', bind_port=1812).start()
