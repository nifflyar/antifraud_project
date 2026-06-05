
from enum import Enum



from app.domain.common.vo.integer import PositiveInteger



class UploadId(PositiveInteger):
    pass


class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
