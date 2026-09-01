from src.agents.memory import MemoryAgent
from src.agents.validation import ValidationAgent


class Orchestrator:
    """Coordinates the overall companion loop."""

    def __init__(self, memory_agent: MemoryAgent, validation_agent: ValidationAgent) -> None:
        self.memory_agent = memory_agent
        self.validation_agent = validation_agent

    def handle_turn(self, *args, **kwargs):
        raise NotImplementedError
