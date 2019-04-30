import pytest

from _pytest.recwarn import WarningsRecorder


all_deprecated_warnings = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    warnings_recorder = WarningsRecorder()
    warnings_recorder._module.simplefilter('once')

    with warnings_recorder:
        yield

    deprecated_warnings = [x for x in warnings_recorder.list if x._category_name in ("DeprecationWarning", "PendingDeprecationWarning")]
    all_deprecated_warnings.extend(deprecated_warnings)


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config=None):
    def clean_duplicated(all_deprecated_warnings):
        cleaned_list = []
        seen = set()

        for warning in all_deprecated_warnings:
            triplet = (warning.filename, warning.lineno, warning.category)

            if triplet in seen:
                continue

            seen.add(triplet)
            cleaned_list.append(warning)

        return sorted(cleaned_list, key=lambda x: (x.filename, x.lineno))

    yield
    print("")
    print("Deprecated warnings summary:")
    for warning in clean_duplicated(all_deprecated_warnings):
        print("* %s:%s %s('%s')" % (warning.filename, warning.lineno, warning.category.__name__, warning.message))

    print("")
    print("All DeprecationWarning errors can be found in the deprecated_warnings.log file.")

    with open("deprecated_warnings.log", "w") as f:
        for warning in clean_duplicated(all_deprecated_warnings):
            f.write("%s:%s %s('%s')\n" % (warning.filename, warning.lineno, warning.category.__name__, warning.message))
