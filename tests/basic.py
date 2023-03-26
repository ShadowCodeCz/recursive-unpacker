import os
import glob
import shutil
import pytest
import recursive_unpacker

test_dir = "./tmp"


class TestInput:
    def __init__(self, archive_path):
        self.archive_path = archive_path

    @property
    def id(self):
        return os.path.basename(self.archive_path)


test_text_file_inputs = [TestInput(test_archive) for test_archive in glob.glob("test_archives/test_file*")]

test_text_file_parameters = [ti.archive_path for ti in test_text_file_inputs]
test_text_file_ids = [ti.id for ti in test_text_file_inputs]


def setup():
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)


@pytest.mark.parametrize("archive_path", test_text_file_parameters, ids=test_text_file_ids)
def test_text_file_unpacked(archive_path):
    setup()

    unpacker = recursive_unpacker.RecursiveUnpacker()
    test_archive = os.path.join(test_dir, os.path.basename(archive_path))
    shutil.copy(archive_path, test_archive)

    unpacker.unpack(test_archive, test_dir)

    search = glob.glob(os.path.join(test_dir, "**/test_file.txt"), recursive=True)

    assert len(search) == 1
    text_file = search[0]

    assert os.path.isfile(text_file)

    with open(text_file) as ftx:
        content = ftx.read()
        assert content.strip() == "test content"


test_complex_inputs = [TestInput("./test_archives/test_file_complex.tar")]

test_complex_parameters = [ti.archive_path for ti in test_complex_inputs]
test_complex_ids = [ti.id for ti in test_complex_inputs]


def check_file(path, content):
    if not os.path.exists(path) and os.path.isfile(path):
        return False

    with open(path, "r") as file:
        return True if file.read().strip() == content else False


@pytest.mark.parametrize("archive_path", test_complex_parameters, ids=test_complex_ids)
def test_complex_structure(archive_path):
    setup()

    unpacker = recursive_unpacker.RecursiveUnpacker()
    test_archive = os.path.join(test_dir, os.path.basename(archive_path))
    shutil.copy(archive_path, test_archive)

    unpacker.unpack(test_archive, test_dir)

    complex_dir = os.path.join(test_dir, "test_file_complex.unpack-tar")

    checks = [
        check_file(os.path.join(complex_dir, "directory1.unpack-7z", "directory2", "test_file_2.txt"), "test content 2"),
        check_file(os.path.join(complex_dir, "directory1.unpack-7z", "test_file.txt"), "test content"),
        check_file(os.path.join(complex_dir, "directory1.unpack-7z", "test_file_1.txt"), "test content 1"),
        check_file(os.path.join(complex_dir, "directory1.unpack-7z", "test_file_3.txt"), "test content 3"),
        check_file(os.path.join(complex_dir, "directory3", "test_file_3.txt"), "test content 3"),
        check_file(os.path.join(complex_dir, "test_file_4.txt"), "test content 4"),
        check_file(os.path.join(complex_dir, "test_file_5.unpack-rar", "test_file_5.txt"), "test content 5"),
        check_file(os.path.join(complex_dir, "test_file_5.unpack-zip", "test_file_5.txt"), "test content 5"),
    ]

    assert sum(checks)



