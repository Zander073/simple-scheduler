from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @abstractmethod
    def infer(self, **kwargs):
        pass 