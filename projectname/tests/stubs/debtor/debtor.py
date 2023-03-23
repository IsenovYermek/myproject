from projectname.tests.stubs.celery_stub import app
from projectname.fails.common import ProgressCounter
from projectname.tests.stubs.debtor.models.profile import DebtorMainProfile
from projectname.tests.stubs.documents.models import Document
from projectname.tests.stubs.documents.serializers import RenderExtractFromEgrnArchiveSerializer
from projectname.tests.stubs.documents.tasks.services import filename_lookup
from projectname.tests.stubs.documents.uuids import (
    CREATE_EGRN_ARCHIVE_UUID,
    CREATE_EGRN_ARCHIVE_ARCHIVE_UUID,
)
from projectname.tests.stubs.notify.models import Notify