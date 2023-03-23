import unittest
from unittest.mock import MagicMock
from projectname.fails.code import create_location_archive, assemble_filename, ExtractFromEgrnTransferOfRights, \
    ExtractFromEgrn, logger

ExtractFromEgrn, logger

# этот тест проверяет поведение кода в случае когда файл не найден.
# для углубленного тестирования необходим доступ ко всему проекту ко всем модулям и базе данных для успешного импорта в тестовый код
# так как из проекта только два файла то не получилось импортировать кое какие модули поэтому пришлось ставить заглушки чтобы код сработал


class TestCreateLocationArchive(unittest.TestCase):
    def setUp(self):
        self.location = 'Moscow'
        self.filename_parts = ['cadastre_number', 'extract_type', 'date']
        self.documents = [
            MagicMock(
                file=MagicMock(
                    name='file.pdf',
                    path='/path/to/file.pdf',
                ),
                cadastre_number='77:01:0000000:0000',
                extract_type='egrn',
                date='2022-06-22'
            ),
            MagicMock(
                file=MagicMock(
                    name='file.pdf',
                    path='/path/to/another/file.pdf',
                ),
                cadastre_number='77:02:0000000:0000',
                extract_type='egrn_transfer_of_rights',
                date='2022-06-23'
            ),
            None,
        ]

    def test_assemble_filename(self):
        test_key = 'fake_key123'
        filename_lookup = {
            'part1': lambda document: test_key,
            'part2': lambda document: 'real_key456',
            'part3': lambda document: 'another_real_key789'
        }
        filename_parts = ['part1', 'part2', 'part3']
        document = ExtractFromEgrnTransferOfRights()

        # Проверяем, что для каждого ключа значение является функцией
        for key, value in filename_lookup.items():
            if not callable(value):
                raise TypeError(f"Value of {key} should be a function")


        result = 'some value'