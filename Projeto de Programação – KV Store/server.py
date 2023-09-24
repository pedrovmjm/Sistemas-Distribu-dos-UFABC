import socket
import json
import threading
from message import Message
import time

class Server:
    
    def __init__(self):
        """
        Inicializa um objeto da classe Server.
        """
        self.ip = "127.0.0.1"
        self.port = None
        self.leaderIp = self.ip 
        self.portaLider = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.portasValidas = [10097, 10098, 10099]
        self.isLider = None
        self.map = {}
        
    def put(self, key, value):
        """
        Armazena um valor no dicionário usando a chave fornecida.

        Args:
            key (str): A chave a ser associada ao valor.
            value (str): O valor a ser armazenado, o valor é um tupla (value,timestamp)
        """
        self.map[key] = value

    def get(self, key):
        """
        Retorna o valor associado à chave fornecida.
        Returns:
            str or None: O valor associado à chave, ou None se a chave não existir no dicionário.
        """
        if key in self.map:
            return self.map[key]
        return None

    def setPortSettings(self):
        """
        Configura as definições de porta do servidor.
        Verifica a disponibilidade dos servidores e obtém a porta do líder do cluster.
        """
        portaLider = None
        activePorts = []
        for port in self.portasValidas:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.connect((self.ip, port))
                    sock.sendall(json.dumps(Message("isLider", None).to_json()).encode())  
                    isLider = sock.recv(1024).decode()
                    message = Message.from_json(json.loads(isLider))
                    if(message.value == True):
                        portaLider = port
                        activePorts.append(port)
                    else:
                        activePorts.append(port)
                except Exception as e:
                    pass
        self.setPort(activePorts)
        self.setportaLider(portaLider)

    def setportaLider(self, portaLider):
        """
        Define a porta do servidor líder do cluster. E faz verificações
        sobre portas validas do lider
        """
        while True:
            try:
                inputPort = int(input("Digite o número da porta do servidor Líder: "))
                if inputPort in self.portasValidas:
                    if portaLider == None:  
                        if inputPort == self.port:
                            self.isLider = True
                            break
                    else:
                        if inputPort == portaLider:
                            self.isLider = False
                            self.portaLider = inputPort
                            break
                else:
                    print("Porta inválida ou já utilizada")
            except ValueError:
                pass
        
    def setPort(self, activePorts):
        """
        Define a porta do servidor e faz verificação para ver a porta já
        está sendo utilizada e se ela é valida
        """
        while True:
            try:
                inputPort = int(input("Digite a porta do servidor: "))
                if inputPort in self.portasValidas:
                    if not (inputPort in activePorts):
                        self.port = inputPort
                        break
                else:
                    print("Porta inválida ou já utilizada")
            except ValueError:
                pass

    def start(self):
        """
        Inicia o servidor. Utiliza threads  para lidar com diversas requisições
        """
        self.setPortSettings()

        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        print(f"Servidor escutando {self.ip}:{self.port}")
        while True:
            conn, addr = self.socket.accept()
            threading.Thread(target=self.handleClients, args=(conn, addr)).start()
        
    def handleClients(self, conn, addr):
        """
        Lida com as solicitações dos clientes. Dependendo de cada método
        Método IsLider, manda menssagem se ou não lider
        Método PUT, manda a mensagem para a função doPut
        Método Get, manda a mensagem para a função doGet
        Método REPLICATION, ativa o doReplication que fará a replicação dos dados
        E posteriormente fecha a conexão para não consumir recursos
        """
        data = conn.recv(1024).decode()
        message = Message.from_json(json.loads(data))

        if message.method == "isLider":
            response = self.isLider
            response_message = Message("isLiderResponse", response)
            conn.sendall(json.dumps(response_message.to_json()).encode())
            
        elif message.method == "PUT":
            self.doPut(conn, message)
            
        elif message.method == "GET":
            self.doGet(conn, message)
        elif message.method == "REPLICATION":
            self.doReplication(conn, message)
            
        conn.close()

    
    def doReplication(self, conn, message):
        """
        Realiza a replicação de dados, após receber uma requisição REPLICATION
        e envia de volta REPLICATION_OK, quando armazenar em sua estrutura local
        """
        valor = message.value[0]
        timestamp= message.value[1]
        chave= message.key
        
        print(f"REPLICATION key:{chave} value:{valor} ts:{timestamp}.")

        if chave in self.map:
            self.map[chave] = (valor, timestamp)
        else:
            self.put(chave, (valor, timestamp))


        conn.sendall(json.dumps(Message("REPLICATION_OK", valor, chave ,timestamp).to_json()).encode())
        
    def doGet(self, conn, message):
        """
        Processa uma solicitação GET.
        -Caso o cliente não tenha a chave em sua estrutura local e pedir um get dela, ele recebe o timestamp armazenado no servidor, visto na linha (173)
        - Caso não exista essa chave em sua estrutura, o servidor envia NULL ao cliente
        - Caso o cliente tenha um ts maior que do server, ele envia TRY_OTHER_SERVER_OR_LATER
        - Caso esteja tudo correto, envia GET_OK
        """
        item = self.get(message.key)
        
        if(message.value==None and item!=None):
            message.value=item[1]

        if item == None:
            print(f"Cliente {conn.getpeername()[0]}:{conn.getpeername()[1]} GET key:{message.key} ts:None, Meu ts é None, portanto devolvendo NULL")
            conn.sendall(json.dumps(Message("NULL", item, None).to_json()).encode())
        elif item[1] is not None and item[1] < message.value:
            print(f"Cliente {conn.getpeername()[0]}:{conn.getpeername()[1]} GET key:{message.key} ts:{message.value}, Meu ts é {item[1]}, portanto devolvendo TRY_OTHER_SERVER_OR_LATER")
            conn.sendall(json.dumps(Message("TRY_OTHER_SERVER_OR_LATER", None).to_json()).encode())
        else:
            print(f"Cliente {conn.getpeername()[0]}:{conn.getpeername()[1]} GET key:{message.key} ts:{message.value}, Meu ts é {item[1]}, portanto devolvendo GET_OK")
            conn.sendall(json.dumps(Message("GET_OK", item).to_json()).encode())

    def doPut(self, conn, message):
        if(self.isLider):
            print(f"Cliente {conn.getpeername()[0]}:{conn.getpeername()[1]} PUT key:{message.key} value:{message.value}")
            self.doLeaderPut(conn, message)
        else:
            print(f"Encaminhando PUT key:{message.key} value:{message.value}")
            self.doServerPut(conn, message)

    def doServerPut(self, conn, message):
        """
        Um servidor que não é lider processa uma solicitação PUT, mandando a
        menssagem para o lider e pedindo para ele recplicar, ele recebe uma menssagem
        put_ok do lider, e encaminha esse put_ok para o cliente
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    try:
                        sock.connect((self.ip, self.portaLider))
                        sock.sendall(json.dumps(message.to_json()).encode())  
                        replication = sock.recv(1024).decode()
                        response = Message.from_json(json.loads(replication))
                  
                    except Exception as e:
                        pass

        valor = response.value
        chave = response.key
        timestamp= response.timestamp
        conn.sendall(json.dumps(Message("PUT_OK",valor, chave ,timestamp).to_json()).encode())


    def doLeaderPut(self, conn, message):
        """
        O servidor que é lider processa uma solicitação PUT, mandando a
        menssagem REPLICATION para ele mesmo e para outros server, após ele 
        receber a quantidade de mensagem de Replication_OK ele recebe uma menssagem
        put_ok 
        """
        timestamp = time.time()
        valor = message.value
        chave= message.key


        serveResponse = []
        if chave in self.map:
            self.map[chave] = (valor, timestamp)
        else:
            self.put(chave, (valor, timestamp))

        message.method = "REPLICATION"
        message.value = (valor, timestamp)
        message.timestamp=timestamp
        for port in self.portasValidas:
            if port != self.portaLider:
                time.sleep(10)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    try:
                        sock.connect((self.ip, port))
                        sock.sendall(json.dumps(message.to_json()).encode())  
                        serveResponse.append( sock.recv(1024).decode())
                            
                    except Exception as e:
                        pass

        if(len(serveResponse)==3):
            print(f"Enviando PUT_OK ao Cliente {conn.getpeername()[0]}:{conn.getpeername()[1]} da key:{chave} ts:{timestamp}") 
            conn.sendall(json.dumps(Message("PUT_OK",valor, chave ,timestamp).to_json()).encode())             
        
        
Server().start()