import socket
import json
import threading


class Server:
    def __init__(self):
        self.listOfPeers = dict()
        self.port = 1099


    # Função uptade, feita após ser baixado um arquivo
    def uptade(self, peer, addr, data):
        if 'data' in data and 'files' in data['data']:
            files = data['data']['files']
            self.listOfPeers[addr[1]] = files
            peer.sendall(b'UPDATE_OK')
        else:
            print("Estrutura do JSON errada.")

    # Função responsável por procurar quais peers contém o arquivo desejado
    def search(self, peer, data):
        search = data['data']['query']
        resultado = []
        for peers, values in self.listOfPeers.items():
            if search in values:
                resultado.append(str(f"127.0.0.1:{peers}"))
        print(f"Peer 127.0.0.1:{peer.getpeername()[1]}  solicitou arquivo {search}.")
        peer.sendall(str(resultado).encode())

    # Função responsável por verificar se o peer contém realmente o arquivo, antes de estabelecer 
    # a conexão
    def search_download(self, peer, data):
        file = data['data']['filename']
        port = str(data['data']['port'])

        for peers, values in self.listOfPeers.items():
            if file in values and str(port) in str(peers):
                peer.sendall(str("OK").encode())
                break
        else:
            peer.sendall(str("Não encontrado no banco de dados do servidor").encode())


    # Função, responsável por realizar o JOIN na estrutura do servidor
    def join(self, peer, addr, data):
        if 'data' in data and 'files' in data['data']:
            files = data['data']['files']

            self.listOfPeers[addr[1]] = files
            peer.send(b'JOIN_OK')
            print(f"Peer 127.0.0.1:{addr[1]} adicionado com arquivos {files}")
        else:
            print("JSON inválido")

    # Recebimento de dados pelo servidor 
    def receiveData(self, peer):
        data = ""
        while True:
            try:
                received = peer.recv(1024)
                data += received.decode()
            except:
                return data
            

    # Função responsável, por receber todas requisições do peer
    def serverUp(self, peer, addr):
        peer.settimeout(3)
        while True:
            response = self.receiveData(peer)

            # Trata cada ação em uma Thread diferente
            try:
                if response != "":
                    data = json.loads(response)

                    if data['method'] == "JOIN":
                        threading.Thread(target=self.join, args=(peer, addr, data)).start()

                    if data['method'] == "SEARCH":
                        threading.Thread(target=self.search, args=(peer, data)).start()

                    if data['method'] == "UPDATE":
                        threading.Thread(target=self.uptade, args=(peer, addr, data)).start()

                    if data['method'] == "DOWNLOAD_REQUEST":
                        threading.Thread(target=self.search_download, args=(peer, data)).start()

            except json.JSONDecodeError as e:
                print("Erro no datagrama do JSON:", str(e))

    def config(self):
        self.inicializar_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.inicializar_socket.bind(('127.0.0.1', self.port))

    def run(self):
        self.config()
        print(f"Servidor rodando no endereço 127.0.0.1:{self.port}")
        self.inicializar_socket.listen(1)

        while True:
            peer, addr = self.inicializar_socket.accept()
            threading.Thread(target=self.serverUp, args=(peer, addr)).start()



server = Server()
server.run()


