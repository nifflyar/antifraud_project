from dishka import Provider, Scope, provide

from app.application.services.audit import AuditService
from app.domain.audit.repository import IAuditLogRepository


class AuditProvider(Provider):
    """Provider for audit service"""
    scope = Scope.REQUEST

    @provide(scope=Scope.REQUEST)
    def provide_audit_service(self, audit_repository: IAuditLogRepository) -> AuditService:
        """Provide the AuditService implementation"""
        return AuditService(audit_repository)
