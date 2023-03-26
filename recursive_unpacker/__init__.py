import glob
import os
import shutil
import patoolib
import logging
import argparse


class RecursiveUnpacker:
    all_supported_suffixes = (
        ".7z", ".cb7",
        ".ace", ".cba",
        ".adf",
        ".alz",
        ".ape",
        ".a",
        ".arc",
        ".arj",
        ".bz2",
        ".cab",
        ".Z",
        ".cpio",
        ".deb",
        ".dms",
        ".flac",
        ".gz",
        ".tgz",
        ".iso",
        ".lrz",
        ".lha", ".lzh",
        ".lz",
        ".lzma",
        ".lzo",
        ".rpm",
        ".rar", ".cbr",
        ".rz",
        ".shn",
        ".tar", ".cbt",
        ".xz",
        ".zip", ".jar", ".cbz",
        ".zoo"
    )

    blind_logger_name = "_BlindRecursiveUnpacker_"
    default_logger_formatter = '%(asctime)s %(levelname)s [RecursiveUnpacker.%(funcName)s()]: %(message)s'

    def __init__(self, logger_name="RecursiveUnpacker", logger_level=logging.DEBUG):
        self.clean_flag = True
        self.output_directory = None
        self.logger = None
        self.logger_level = logger_level
        self.exclusions = []

        self.prepare_logger(logger_name)

    def prepare_logger(self, logger_name):
        if logger_name:
            self.logger = logging.getLogger(logger_name)
            self._remove_all_logger_handlers()
            self._set_logger_stream_handler()
        else:
            self.logger = logging.getLogger(self.blind_logger_name)
            self._remove_all_logger_handlers()

    def _set_logger_stream_handler(self):
        self.logger.setLevel(self.logger_level)
        formatter = logging.Formatter(self.default_logger_formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self.logger.addHandler(stream_handler)

    def _remove_all_logger_handlers(self):
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)

    def add_exclusions(self, exclusions):
        self.exclusions += exclusions
        self.exclusions = set(exclusions)

    def clean_exclusions(self):
        self.exclusions = []

    @property
    def relative_suffixes(self):
        return [suffix for suffix in self.all_supported_suffixes if suffix not in self.exclusions]

    # TODO: User specific path / filename limitations
    # TODO: Auto prefix or suffix filenames
    def unpack(self, archive, output_directory, clean_flag=True):
        self.output_directory = output_directory
        self.clean_flag = clean_flag

        os.makedirs(output_directory, exist_ok=True)

        if os.path.dirname(archive) != output_directory:
            shutil.copy(archive, output_directory)

        copied_archive = os.path.join(output_directory, os.path.basename(archive))

        self._unpack(copied_archive)
        self._clean()

    def _unpack_archive_directory(self, archive):
        archive_filename_parts = os.path.basename(archive).split(".")
        archive_suffix = archive_filename_parts[-1]
        archive_unpack_dir_name = ".".join(archive_filename_parts[:-1])
        archive_unpack_dir_name = f"{archive_unpack_dir_name}.unpack-{archive_suffix}"

        archive_dir = os.path.dirname(os.path.abspath(archive))
        return os.path.join(archive_dir, archive_unpack_dir_name)

    def _unpack(self, archive):
        self.logger.debug(f"Unpack {archive}")
        try:
            archive_dir = os.path.dirname(os.path.abspath(archive))
            unpack_dir = self._unpack_archive_directory(archive)

            # TODO: Consider finding non conflict directory
            if os.path.exists(unpack_dir):
                self.logger.warning(f"Unpack directory {unpack_dir} already exists.")
            os.makedirs(unpack_dir, exist_ok=True)

            patoolib.extract_archive(archive, outdir=unpack_dir, verbosity=-1)
            self.logger.debug(f"Removing {archive}")
            os.remove(archive)

            self._unpack_sub_archives(archive, archive_dir)

        except Exception as e:
            self.logger.error(f"Unpack archive '{os.path.abspath(archive)}' failed.\n{e}")

    def _unpack_sub_archives(self, archive, archive_dir):
        for sub_archive in self._find_archives_recursively(archive_dir):
            if os.path.abspath(sub_archive) != os.path.abspath(archive):
                self._unpack(sub_archive)

    def _find_archives_recursively(self, dir):
        recursive_dir = os.path.join(dir, "**")
        for suffix in self.relative_suffixes:
            template = os.path.join(recursive_dir, f"*{suffix}")
            yield from glob.glob(template, recursive=True)

    def _clean(self):
        if self.clean_flag:
            for archive in self._find_archives_recursively(self.output_directory):
                if os.path.isfile(archive):
                    self.logger.debug(f"Removing {archive}")
                    os.remove(archive)


def unpack_all(arguments):
    unpacker = RecursiveUnpacker()
    unpacker.logger.setLevel(int(arguments.logger_level))
    unpacker.add_exclusions(arguments.exclusions)

    files = [f for f in os.listdir(".") if os.path.isfile(f)]
    for suffix in unpacker.relative_suffixes:
        for file in files:
            if file.endswith(suffix):
                unpacker.unpack(file, arguments.output_directory)


def unpack_file(arguments):
    unpacker = RecursiveUnpacker()
    unpacker.logger.setLevel(int(arguments.logger_level))
    unpacker.add_exclusions(arguments.exclusions)
    unpacker.unpack(arguments.archive, arguments.output_directory)


def main():
    parser = argparse.ArgumentParser(description="Recursive Unpacker", formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-o", "--output_directory", default="./unpack")
    parser.add_argument("-e", "--exclusions", nargs='+', default=[])
    parser.add_argument("-l", "--logger_level", default=logging.INFO, type=int)

    subparsers = parser.add_subparsers()

    all_parser = subparsers.add_parser('all')
    all_parser.set_defaults(func=unpack_all)
    all_parser.add_argument("-i", "--input_directory", default=".")

    file_parser = subparsers.add_parser('file')
    file_parser.set_defaults(func=unpack_file)
    file_parser.add_argument("-a", "--archive", required=True)

    arguments = parser.parse_args()
    arguments.func(arguments)


