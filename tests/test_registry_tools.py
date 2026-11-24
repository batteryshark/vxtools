from vxtools.pdxreg_tools import anonymize_key_path


def test_anonymize_key_path_removes_user_sid() -> None:
    key_path = r"\registry\user\s-1-5-21-123-456-789-1001\software\game"

    assert anonymize_key_path(key_path) == r"\registry\user\software\game"


def test_anonymize_key_path_keeps_machine_keys() -> None:
    key_path = r"\registry\machine\software\game"

    assert anonymize_key_path(key_path) == key_path
