import socket
import json
import random
import threading
from message import Message
import time


class Client:
    def __init__(self):
        """
        Inicializa um objeto da classe Client.
        """
        self.servers = [('127.0.0.1', 10097), ('127.0.0.1', 10098), ('127.0.0.1', 10099)]
        self.server = None
        self.map = {}

    def doPut(self, key, value):
        """
        Armazena um valor no dicionário usando a chave fornecida.

        Args:
            key (str): A chave a ser associada ao valor.
            value (str): O valor a ser armazenado (timestamp)
        """
        self.map[key] = value


    def doGet(self, key):
        """
        Retorna o valor associado à chave fornecida.
        Verificando se a chave contém na estruta de dados
        """
        if key in self.map:
            return self.map[key]
        return None


    def chooseServer(self):
        """
        Escolhe um servidor aleatório da lista de servidores disponíveis e o define como o servidor atual.
        """
        self.server = random.choice(self.servers)

    def inicializar(self):
        """
        Inicializa o cliente.
        """
        while True:
            userInput = input("Para inicializar digite 'START':")
            if(userInput == "START"):
                while True:
                    self.run()

    
    def requestPut(self, key=None, value=None, timestamp= None):
        """
        Envia uma solicitação PUT para o servidor atual, com a chave, valor e timestamp fornecidos.
        Recebendo a resposta do servidor ele verifica se houve algum erro, se não tiver
        recebe a resposta PUT_OK e salva em sua estrutura de dados local
        """
        message = Message("PUT", key=key, value=value)
        try:
            socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_obj.connect(self.server)
            socket_obj.sendall(json.dumps(message.to_json()).encode())
            response = socket_obj.recv(1024).decode()
            socket_obj.close()
            response = json.loads(response)
        except Exception as e:
            print(f"Error occurred while sending request: {e}")
        if response['method'] == "PUT_OK":
            print(f"\nPUT_OK key: {response['key']} value {response['value']} timestamp {response['timestamp']} realizada no servidor [127.0.0.1:{self.server[1]}].")
            self.doPut(response['key'],response['timestamp'])
        

    def requestGET(self, key):
        """
        Envia uma solicitação GET para o servidor atual, com a chave fornecida.
        Caso não tenha a cahve em sua estruta, define o localTimestamp como None
        Nesse caso, pode receber três respostas do server:
        Primeira: O server não tem a chave
        Segunda: TRY_OTHER_SERVER_OR_LATER, ou seja, devemos fazer a solicitação posterior
        Terceira: GET_OK, e atualiza o valor da estrutura de dados local
        """
        timer = self.doGet(key)
        localTimestamp = None if timer == None else timer
        message = Message("GET", value= timer , key= key)
        try:
            socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_obj.connect(self.server)
            socket_obj.sendall(json.dumps(message.to_json()).encode())
            response = socket_obj.recv(1024).decode()
            socket_obj.close()
            response = json.loads(response)
        except Exception as e:
            print(f"Error occurred while sending request: {e}")

        if response['method'] == "NULL":
            print("\nKEY NOT FOUND")
        elif response['method'] == "TRY_OTHER_SERVER_OR_LATER":
            print("\nTRY_OTHER_SERVER_OR_LATER")
        else:
            self.doPut(key,response['value'][1])
            print(f"\nGET key: {key} value: {response['value'][0]} obtido do servidor [127.0.0.1:{self.server[1]}], meu timestamp {localTimestamp} e do servidor {response['value'][1]}")


    def run(self):
        """
        Executa o cliente.
        """
        while True:
            self.chooseServer()
            print("Opções:")
            print("1. PUT")
            print("2. GET")
            acao = input("Escolha a ação (1-3): ")

            if acao == "1":
                key = input("Digite a chave(Key):")
                value = input("Digite o valor(Value):")
                threading.Thread(target=self.requestPut, args=(key , value)).start()
            elif acao == "2":
                key = input("Digite a chave(Key):")
                threading.Thread(target=self.requestGET, args=(key)).start()
            else:
                print("Opção Inválida")



client = Client()
client.inicializar()

