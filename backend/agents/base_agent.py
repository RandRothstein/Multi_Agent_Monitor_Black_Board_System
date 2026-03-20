from abc import ABC, abstractmethod

class BaseAgent(ABC):

    def __init__(self, db_session,sku_id):
        self.db = db_session
        self.sku_id = sku_id

    @abstractmethod
    def run(self):
        pass