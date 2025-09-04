from dataclasses import asdict
from ..domain.events import MirrorCommand

class LoggingOutbox:
    def __init__(self, sink=print): self.sink=sink
    def enqueue(self, commands:list[MirrorCommand])->None:
        for c in commands: self.sink({"enqueue": asdict(c)})
