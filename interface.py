from abc import ABC, abstractmethod


class BlockchainInterface(ABC):
    @abstractmethod
    def add_block(self):
        pass

    @abstractmethod
    def proof_of_work(self):
        pass


class ClassInterface(ABC):
    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def to_class(self):
        pass
