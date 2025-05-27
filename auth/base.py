from abc import ABC, abstractmethod

class AuthBackend(ABC):
    @abstractmethod
    def authenticate(self, username: str, password: str) -> bool:
        """Doit retourner True si l'utilisateur est authentifié, False sinon."""
        pass
