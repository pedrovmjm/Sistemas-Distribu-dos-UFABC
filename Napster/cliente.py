import socket
import os
import threading
import json


class Peer:
    # Inicializaçao dos parametros
    def __init__(self):
        self.arquivos = []
        self.serverPort = 1099
        self.address_server = '127.0.0.1'
        self.inicializar_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.inicializar_socket.connect((self.address_server, self.serverPort))
        self.clientPort = self.inicializar_socket.getsockname()[1]
        self.pasta_peer = os.path.join(os.getcwd(), "peers")

        if not os.path.isdir(self.pasta_peer):
            os.mkdir(self.pasta_peer)

        self.pasta_peer = os.path.join(self.pasta_peer, str(self.clientPort))
        os.mkdir(self.pasta_peer)
        print("Pasta do cliente: " + self.pasta_peer)


    # Função responsável estabelecer a conexão com o servidor, capturando os arquivos que o peer 
    # quer compartilhar com o servidor e outros peers. Essa função representa o JOIN
    def setup_cliente(self):
        print("O seu nome na rede é: " + str(self.clientPort))
        print("Está conectando no servidor: " + str(self.address_server) + ":" + str(self.serverPort))

        while True:
            print("----------------")
            print("Os arquivos que disponibilizados são:")
            print(os.listdir(self.pasta_peer))
            print("1. Iniciar Conexão")
            print("2. Atualizar os arquivos")
            print("----------------")

            entrada = input()
            if entrada == "1":
                break

        self.arquivos = os.listdir(self.pasta_peer)
        arquivos_formatados = ['"{}"'.format(item) for item in self.arquivos]
        arquivos_concatenados = ','.join(arquivos_formatados)
        message = '''{{"method": "JOIN", "data": {{"files": [{files}]}}}}'''.format(files=arquivos_concatenados)
        self.inicializar_socket.sendall(message.encode())

        if self.inicializar_socket.recv(1024).decode() == "JOIN_OK":
            print(f"Sou peer {self.address_server}:{self.clientPort} com arquivos:[{arquivos_concatenados}]")
        else:
            print("Falha na conexão!")

    
    # Função responsável por receber a a requisição de download de outro peer
    # Verifica se o peer contém esse arquivo, se não tiver retorna FILE_NOT_FOUD
    # Se sim, permite o peer compartilhar ou não, se quiser compartilhar
    # retorna um OK e inicia a transferência
    # E fecha o socket no final, a velocidade de envio é dada pela linha 85 e foi abritrária 
    def download_peer(self, client_socket):
        request = client_socket.recv(1024).decode()
        data = json.loads(request)
        filename = data["data"]["filename"]
        peer = data["data"]['port']

        pasta_peer = os.path.join(os.getcwd(), "peers")
        peer_folder = os.path.join(pasta_peer, str(peer))
        if filename in os.listdir(peer_folder):
            file_path = os.path.join(peer_folder, filename)
            file_size = os.path.getsize(file_path)

            while True:
                user_response = input("Você recebeu uma solicitação de download de um peer. Deseja aceitar? (Digite 'SIM' ou 'NAO'). Ignore outras mensagem do terminal\n")
                if user_response.upper() == "SIM" or user_response.upper() == "NAO":
                    response = {"status": "OK", "file_size": file_size, "data": user_response}
                    client_socket.send(json.dumps(response).encode())
                    break
                else:
                    print("Resposta inválida! Digite 'SIM' ou 'NAO'. Ignore outras mensagem do terminal")

            if(response["data"]=="SIM"):
                with open(file_path, "rb") as file:
                    while True:
                        data = file.read(1024*1024*5)
                        if not data:
                            break
                        client_socket.send(data)

        else:
            response = {"status": "FILE_NOT_FOUND"}
            client_socket.send(json.dumps(response).encode())

        client_socket.close()

    # Responsável por fazer o peer escutar outros peers e aceitar conexões
    def request_peers(self):
        download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        download_socket.bind(('127.0.0.1', self.clientPort))
        download_socket.listen(5)

        while True:
            client_socket, _ = download_socket.accept()
            # Lidar com a solicitação de download em uma nova thread
            threading.Thread(target=self.download_peer, args=(client_socket,)).start()

    def comandos_cliente(self, un):
        print("Insira algum dos comandos aceitos: \n - SEARCH \n - DOWNLOAD \n")
        entrada = input().upper()

        if entrada == "SEARCH":
            entrada = input("Insira o arquivo que deseja buscar:\n")
            message = '''{"method":"SEARCH","data":{"query":"%s"}}''' % entrada

            # Envia json com os arquivos que é necessário buscar
            self.inicializar_socket.sendall(message.encode())
            print(f"Peers com arquivo solicitado: {self.inicializar_socket.recv(1024).decode()} ")

        elif entrada == "DOWNLOAD":
            arquivo = input("Insira o nome do arquivo que deseja baixar:\n")
            endereco_peer_arquivo = int(input("Insira a porta do peer a partir do qual deseja baixar o arquivo:\n"))
            message = '''{{"method": "DOWNLOAD_REQUEST", "data": {{"filename": "{}", "port": {}}}}}'''.format(arquivo, endereco_peer_arquivo)

            # Envia json para verificar com o servidor se o peer tem o arquivo ou não
            self.inicializar_socket.sendall(message.encode())

            # Após receber a informação do servidor, se a resposta for OK, inicia o processo de conexão com outro peer
            resposta = self.inicializar_socket.recv(1024).decode()
            if resposta =="OK":
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((self.address_server, endereco_peer_arquivo))


                # Enviar solicitação de download para o peer
                message = '''{{ "data": {{"filename": "{}", "port": {}}}}}'''.format(arquivo, endereco_peer_arquivo)
                peer_socket.sendall(message.encode())

                # Recebe resposta do peer para verificar se ele contém realmente o arquivo e se ele quer compartilhar
                response = peer_socket.recv(1024).decode()
                response_data = json.loads(response)
                if response_data["status"] == "OK" and response_data['data']=="SIM":
                    file_size = response_data["file_size"]
                    received_data = b""
                    bytes_received = 0

                    # Recebendo os dados e verificando o tamanho do arquivo
                    while bytes_received < file_size:
                        data = peer_socket.recv(1024*1024*5)
                        received_data += data
                        bytes_received += len(data)

                     # Gravando os dados recebidos 
                    caminho_arquivo = os.path.join(self.pasta_peer, arquivo)
                    with open(caminho_arquivo, "wb") as file:
                        file.write(received_data)

                    print(f"Arquivo {arquivo} baixado com sucesso na pasta {caminho_arquivo}")

                    # Lista os arquivos no peer
                    self.arquivos = os.listdir(self.pasta_peer)
                    arquivos_formatados = ['"{}"'.format(item) for item in self.arquivos]
                    arquivos_concatenados = ','.join(arquivos_formatados)
                    message = '''{{"method": "UPDATE", "data": {{"files": [{files}]}}}}'''.format(files=arquivos_concatenados)

                    # Envia json com os arquivos do peer ao servidor
                    self.inicializar_socket.sendall(message.encode())
                    resposta_uptade = self.inicializar_socket.recv(1024).decode()
                    if(resposta_uptade=="UPDATE_OK"):
                        pass
                    else:
                        print("Erro no uptade")

                else:
                    print("Peer não quer compartilhar ou não contém o arquivo")

            else:
                print("Arquivo ou peer não encontrado")

        elif(entrada==""):
            pass
        else:
            print("Comando não reconhecido")

        threading.Thread(target=self.comandos_cliente, args=(un,)).start()


# Inicilização de todos os processos e criação de Threads
if __name__ == "__main__":
    cliente = Peer()
    cliente.setup_cliente()

    try:
        threading.Thread(target=cliente.request_peers).start()
        threading.Thread(target=cliente.comandos_cliente, args=(cliente.inicializar_socket,)).start()
        threading.Event().wait()
    except Exception as e:
        print("Ocorreu um erro:", str(e))
    finally:
        cliente.inicializar_socket.close()
