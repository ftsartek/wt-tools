import json
import logging
from pathlib import Path
import pytest
from pytest_lazyfixture import lazy_fixture
from src.wt_tools.vromfs_unpacker import unpack

# from wt_tools.vromfs_unpacker import unpack
from tests.helpers import check_path, make_tmppath

tmppath = make_tmppath(__name__)


@pytest.fixture(scope="module")
def nm_version_file_list_path(tmppath):
    path = tmppath / "nm_version.json"
    data = ["version", "nm"]

    with open(path, "w") as ostream:
        json.dump(data, ostream)
    return path


nm_version_file_list_path_ = lazy_fixture("nm_version_file_list_path")


@pytest.mark.parametrize(
    "file_list_path",
    [
        pytest.param(
            None, id="all"
        ),  # Test case where no specific file list is provided
        pytest.param(nm_version_file_list_path_, id="nm_version"),
        # Test case where a specific file list is provided
    ],
)
def test_unpack_wt(wtpath, file_list_path: Path, tmp_path):
    logging.info(f"dst path: {tmp_path}")

    # Ensure wtpath exists & collect all vromfs.bin files in that directory. If none are found, skip the test.
    check_path(wtpath, "wtpath")
    image_paths = tuple(wtpath.rglob("*.vromfs.bin"))
    if not image_paths:
        pytest.skip(
            "Directory does not contain any .vromfs.bin files: {}".format(wtpath)
        )

    for src_path in image_paths:
        # Get the relative path of the source file
        rel_src_path = src_path.relative_to(wtpath)
        logging.info(f"image: {rel_src_path}")

        # Create a destination path by removing the file extension from the source path
        dst_path = tmp_path / rel_src_path.with_suffix("").with_suffix("")

        # Unpack the source file to the destination path
        written_names = unpack(src_path, dst_path, file_list_path)

        # If a file list is provided, check that the number of unpacked files is less than or equal to the file list
        if file_list_path:
            file_list = json.load(file_list_path.open())
            assert len(written_names) <= len(file_list)
        else:
            # If no file list is provided, check that some files were unpacked
            assert written_names

        # Calculate the total size of the unpacked files
        size = 0
        for name in written_names:
            path = dst_path / name
            stat = path.stat()
            assert stat.st_size
            size += stat.st_size

        # Log the total number of files and their size
        logging.info(f"total: {len(written_names):_} files, {size:_} bytes")
