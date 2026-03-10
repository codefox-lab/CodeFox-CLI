import abc


class BaseCLI(abc.ABC):
    @abc.abstractmethod
    def execute(self) -> None:
        pass
