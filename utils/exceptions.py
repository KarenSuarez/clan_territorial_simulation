# clan_territorial_simulation/utils/exceptions.py
class SimulationError(Exception):
    """Base class for simulation-related exceptions."""
    pass

class ConfigurationError(SimulationError):
    """Exception raised for invalid simulation configurations."""
    pass

class DataError(SimulationError):
    """Exception raised for issues with data loading or processing."""
    pass

class RenderingError(SimulationError):
    """Exception raised for errors during visualization rendering."""
    pass

class AnalysisError(SimulationError):
    """Exception raised for errors during scientific analysis."""
    pass