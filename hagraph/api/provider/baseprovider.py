"""
BaseProvider
Subclassed by every *real* provider
"""
from hagraph.api.client import GraphApiClient


class BaseProvider:
    def __init__(self, client: GraphApiClient):
        """
        Initialize an the BaseProvider
        Args:
            client (:class:`GraphApiClient`): Instance of GraphApiClient
        """
        self.client = client