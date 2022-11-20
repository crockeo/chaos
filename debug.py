from pathlib import Path


def cat_dir(dir_path: Path, *, indent: int = 0) -> None:
    for file_path in dir_path.iterdir():
        if file_path.is_dir():
            pass

        print("=" * len(file_path.name))
        print(file_path.name)
        print("=" * len(file_path.name))
        if file_path.is_dir():
            # TODO: print sub-dir at some point
            pass
            cat_dir(file_path, indent=indent + 4)
        else:
            contents = file_path.read_text()
            print(contents)
