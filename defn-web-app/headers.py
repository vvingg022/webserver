import typing
from collections import defaultdict

HeadersGenerator = typing.Generator[typing.Tuple[str, str], None, None]


class Headers:
    """Case-insensitive header names, each mapped to a list of values."""

    def __init__(self) -> None:
        self._headers = defaultdict(list)

    def add(self, name: str, value: str) -> None:
        self._headers[name.lower()].append(value)

    def get_all(self, name: str) -> typing.List[str]:
        # .get() avoids creating an empty entry just because we looked.
        return list(self._headers.get(name.lower(), []))

    def get(self, name: str, default: typing.Optional[str] = None) -> typing.Optional[str]:
        values = self.get_all(name)
        return values[-1] if values else default

    def __iter__(self) -> HeadersGenerator:
        for name, values in self._headers.items():
            for value in values:
                yield name, value

    def __repr__(self) -> str:
        return f"Headers({dict(self._headers)})"