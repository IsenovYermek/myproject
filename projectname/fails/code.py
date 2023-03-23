import re
import os
import logging
import zipfile
import unicodedata
from io import BytesIO
from dateutil import parser
from collections import defaultdict
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from django.db.models import Exists, OuterRef, Subquery
from django.utils import timezone
from projectname.fails.common import ProgressCounter
from projectname.datafile.tasks import BaseTask

try:
    from config.celery import app as celery_app
except ImportError:
    from projectname.tests.stubs.celery_stub import app as celery_app

logger = logging.getLogger('documents')


class ExtractFromEgrnTransferOfRights:
    pass
CREATE_EGRN_ARCHIVE_UUID = ''
CREATE_EGRN_ARCHIVE_ARCHIVE_UUID = ''


class ExtractFromEgrn:
    pass
# Этот отрезок кода был закомментирован так для теста этого файла необходим доступ к базе данных

def assemble_filename(
    filename_parts: list[str],
    document: ExtractFromEgrnTransferOfRights | ExtractFromEgrn,
filename_lookup=None) -> str:
    """Собирает имя файла по частям"""
    if not filename_parts:
        return os.path.basename(document.file.name)
    parts: list[str] = [filename_lookup[part](document) for part in filename_parts]
    ext = document.file.name.split('.')[-1]
    return f'{"_".join(parts)}.{ext}'


def get_date_from(data_package) -> datetime | None:
    """Достает из пакета date_from"""
    return (
        parser.parse(data_package.payload['date_from'])
        if data_package.payload and data_package.payload.get('date_from')
        else None
    )


def get_date_to(data_package) -> datetime | None:
    """Достает из пакета date_to"""
    return (
        parser.parse(data_package.payload['date_to'])
        + timedelta(hours=23, minutes=59, seconds=59)
        if data_package.payload and data_package.payload.get('date_to')
        else None
    )


def slugify(value: str) -> str:
    """Нормализует и преобразует строку к slug"""
    value = unicodedata.normalize('NFKC', value)
    value = re.sub(r'[^\w\s-]', '', value)

    return re.sub(r'[-\s]+', '-', value).strip('-_')


def create_location_archive(
    location: str,
    filename_parts: list[str],
    documents: list[ExtractFromEgrnTransferOfRights, ExtractFromEgrn],
) -> str:
    """
    Создает архив выписок, которые принадлежат указанной локации и возвращает его название
    """
    buffer = BytesIO()
    zip_file = zipfile.ZipFile(buffer, "w")
    for document in documents:
        if document:
            try:
                zip_file.write(
                    document.file.path, assemble_filename(filename_parts, document)
                )
            except (FileNotFoundError, ValueError):
                logger.error(
                    msg=f"File {document.file.path} not found. Skip it.",
                )
                continue
    zip_file.close()
    buffer.seek(0)
    filename = f'{slugify(location)}_{timezone.now()}.zip'
    with open(filename, 'wb') as archive_file:
        while data := buffer.read(1024 * 1024):
            archive_file.write(data)
    buffer.close()

    return filename


class ExtractFromEgrnArchive:
    pass


class Debtor:
    pass


class CreateExtractFromEgrnArchiveTask(BaseTask):
    uuid = CREATE_EGRN_ARCHIVE_UUID
    name = 'Формирование архива выписок ЕГРН'
    progress_class = ProgressCounter

    def on_start(self):
        self.obj = {}

    def _execute(self):
        date_filters = {}
        date_from = get_date_from(self.data_package)
        date_to = get_date_to(self.data_package)
        filename_parts = self.data_package.payload['filename_parts']

        if date_from and date_to:
            archive, created = ExtractFromEgrnArchive.objects.get_or_create(
                company_id=self.data_package.company_id,
                date_from=date_from,
                date_to=date_to,
                defaults={'file': ContentFile(b'', name=f'egrn_archive.zip')},
            )
            if not created:
                self.obj = {"url": archive.file.url}
                return True
            date_filters = {
                'created_at__gte': date_from,
                'created_at__lte': date_to,
            }
        else:
            archive, _ = ExtractFromEgrnArchive.objects.get_or_create(
                company_id=self.data_package.company_id,
                date_from=None,
                date_to=None,
                defaults={'file': ContentFile(b'', name=f'egrn_archive.zip')},
            )
        debtors = Debtor.objects.filter(
            Exists(
                ExtractFromEgrn.objects.filter(
                    debtor_id=OuterRef('id'),
                    ftype=ExtractFromEgrn.PDF,
                    **date_filters,
                )
                .exclude(file="")
                .order_by('-status_tracking_id')
            )
            | Exists(
                ExtractFromEgrnTransferOfRights.objects.filter(
                    debtor_id=OuterRef('id'),
                    ftype=ExtractFromEgrnTransferOfRights.PDF,
                    **date_filters,
                )
                .exclude(file="")
                .order_by('-status_tracking_id')
            ),
            company_id=self.data_package.company_id,
        )
        self.set_max(debtors.count())
        buffer = BytesIO()
        zip_file = zipfile.ZipFile(buffer, "w")
        for debtor in debtors:
            documents = (
                ExtractFromEgrn.objects.filter(
                    debtor=debtor,
                    ftype=ExtractFromEgrn.PDF,
                    **date_filters,
                )
                .exclude(file="")
                .order_by('-status_tracking_id')
                .first(),
                ExtractFromEgrnTransferOfRights.objects.filter(
                    debtor=debtor,
                    ftype=ExtractFromEgrnTransferOfRights.PDF,
                    **date_filters,
                )
                .exclude(file="")
                .order_by('-status_tracking_id')
                .first(),
            )
            for document in documents:
                if document:
                    try:
                        zip_file.write(
                            document.file.path,
                            assemble_filename(filename_parts, document),
                        )
                    except (FileNotFoundError, ValueError):
                        logger.warning(
                            msg=f"File {document=} for {debtor=} not found. Skip it.",
                        )
                        continue
            self.next_step()
        zip_file.close()
        buffer.seek(0)
        with open(archive.file.path, 'wb') as archive_file:
            while data := buffer.read(1024 * 1024):
                archive_file.write(data)
        buffer.close()
        self.obj = {"url": archive.file.url}
        return True