from dishka import Provider, Scope, provide

from app.infrastructure.config import Config
from app.infrastructure.ml_client import MlServiceClient


class MlProvider(Provider):
    @provide(scope=Scope.APP)
    def get_ml_client(self, config: Config) -> MlServiceClient:
        return MlServiceClient(
            base_url=config.ml.url,
            timeout=config.ml.timeout,
        )
