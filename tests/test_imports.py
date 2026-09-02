"""Smoke testy importów pakietów projektu."""


def test_import_main_packages() -> None:
    import src  # noqa: F401
    import src.core  # noqa: F401
    import src.io_adapters  # noqa: F401
    import src.ui  # noqa: F401
    import src.features  # noqa: F401
    import src.features.f02_ifc_validation  # noqa: F401
    import src.features.f03_ifc_metadata  # noqa: F401
    import src.features.f04_ifc_classes  # noqa: F401
    import src.features.f06_report  # noqa: F401


def test_import_app_entrypoint() -> None:
    import app  # noqa: F401
