from dishka import Provider, Scope, provide

from app.application.audit import ListAuditLogsInteractor, GetAuditLogInteractor
from app.domain.audit.repository import IAuditLogRepository


class AuditInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_list_audit_logs_interactor(
        self,
        audit_repository: IAuditLogRepository,
    ) -> ListAuditLogsInteractor:
        return ListAuditLogsInteractor(audit_repository)

    @provide
    def provide_get_audit_log_interactor(
        self,
        audit_repository: IAuditLogRepository,
    ) -> GetAuditLogInteractor:
        return GetAuditLogInteractor(audit_repository)
