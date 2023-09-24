class Message:
    
    """
        Uma classe que representa um objeto de mensagem.

        Atributos:
            method (str): O método da mensagem.
            value (str): O valor da mensagem.
            key (str, opcional): A chave associada à mensagem (padrão é None).
            timestamp (str, opcional): O timestamp da mensagem (padrão é None).
    """

    def __init__(self, method, value, key=None, timestamp=None):
        """
        Inicializa um objeto da classe Message.
        """
        self.method = method
        self.value = value
        self.key=key
        self.timestamp= timestamp

    def __str__(self):
        """
            Retorna uma representação em string do objeto Message.
        """
        return f"Message: method={self.method}, value={self.value}, key={self.key}, timestamp={self.timestamp}"


    def to_json(self):
        """
        Converte o objeto Message em um objeto JSON.
        """
        return {
            "method": self.method,
            "value": self.value,
            "key": self.key,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_json(cls, json_data):
        """
        Cria um objeto Message a partir de um objeto JSON.

        O decorador @classmethod em Python diz ao Python que o método from_json() 
        é um método de classe. Isso significa que o método pode ser chamado na classe em si, 
        em vez de em uma instância da classe.
        """
        return cls(json_data["method"], json_data["value"],json_data["key"],json_data["timestamp"])