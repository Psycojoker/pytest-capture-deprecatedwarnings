import os
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

    for i in deprecated_warnings:
        i.item = item

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

    pwd = os.path.realpath(os.curdir)

    def cut_path(path):
        if path.startswith(pwd):
            return path[len(pwd) + 1:]
        return path

    def format_test_function_location(item):
        return "%s::%s:%s" % (item.location[0], item.location[2], item.location[1])

    yield
    if all_deprecated_warnings:
        print("")
        print("Deprecated warnings summary:")
        print("============================")
        for warning in clean_duplicated(all_deprecated_warnings):
            print("%s\n-> %s:%s %s('%s')" % (format_test_function_location(warning.item), cut_path(warning.filename), warning.lineno, warning.category.__name__, warning.message))

        print("")
        print("All DeprecationWarning errors can be found in the deprecated_warnings.log file.")

        with open("deprecated_warnings.log", "w") as f:
            for warning in clean_duplicated(all_deprecated_warnings):
                f.write("%s\n-> %s:%s %s('%s')\n" % (format_test_function_location(warning.item), cut_path(warning.filename), warning.lineno, warning.category.__name__, warning.message))
    else:
        # nothing, clear file
        with open("deprecated_warnings.log", "w") as f:
            f.write("")
