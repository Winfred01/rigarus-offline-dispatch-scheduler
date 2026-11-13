from dataclasses import dataclass

MAXIMUM_NOTE_LENGTH = 200


@dataclass(frozen=True)
class DemoProject:
    id: int
    job_number: str
    site_name: str
    note: str


def validate_note(note: str) -> None:
    try:
        length = len(note.encode("utf-16-le")) // 2
    except UnicodeEncodeError as error:
        raise ValueError("The demo note must contain valid Unicode text.") from error
    if length > MAXIMUM_NOTE_LENGTH:
        raise ValueError("The demo note must be 200 characters or fewer.")
