from dishka import Provider, Scope, provide

from app.application.upload.create_upload import CreateUploadInteractor
from app.application.upload.get_upload import GetUploadInteractor
from app.application.upload.list_uploads import ListUploadsInteractor


from app.application.common.transaction import TransactionManager
from app.application.services.audit import AuditService
from app.domain.upload.repository import IUploadRepository

class UploadInteractorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_create_upload_interactor(
        self,
        upload_repository: IUploadRepository,
        audit_service: AuditService,
        transaction_manager: TransactionManager,
    ) -> CreateUploadInteractor:
        return CreateUploadInteractor(
            upload_repository=upload_repository,
            audit_service=audit_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def provide_get_upload_interactor(
        self, upload_repository: IUploadRepository
    ) -> GetUploadInteractor:
        return GetUploadInteractor(upload_repository=upload_repository)

    @provide
    def provide_list_uploads_interactor(
        self, upload_repository: IUploadRepository
    ) -> ListUploadsInteractor:
        return ListUploadsInteractor(upload_repository=upload_repository)
