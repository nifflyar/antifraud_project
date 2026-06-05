from dishka import Provider, Scope, provide
from app.infrastructure.config import Config


class ConfigProvider(Provider):
    scope = Scope.APP

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    @provide
    def get_config(self) -> Config:
        return self.config