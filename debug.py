from pathlib import Path


def cat_dir(dir_path: Path, *, indent: int = 0) -> None:
    for file_path in dir_path.iterdir():
        if file_path.is_dir():
            pass

        indent_text = " " * indent
        print(indent_text, "=" * len(file_path.name), sep="")
        print(indent_text, file_path.name, sep="")
        print(indent_text, "=" * len(file_path.name), sep="")
        if file_path.is_dir():
            cat_dir(file_path, indent=indent + 4)
        else:
            contents = file_path.read_text()
            lines = [f"{indent_text}{line}" for line in contents.splitlines()]
            print("\n".join(lines))
            print()
