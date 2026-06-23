import sys
from pathlib import Path

from shared.services.openstack import SwiftClient


def main() -> None:
    container, object_name, file_path = sys.argv[1:4]
    SwiftClient().upload(container, object_name, Path(file_path))


if __name__ == "__main__":
    main()
