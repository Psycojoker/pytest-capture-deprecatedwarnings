import os
import sys
import json
import pytest

from _pytest.recwarn import WarningsRecorder

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


all_deprecated_warnings = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """
    Needed to grab the item.location information
    """
    warnings_recorder = WarningsRecorder()
    warnings_recorder._module.simplefilter('once')

    with warnings_recorder:
        yield

    deprecated_warnings = [x for x in warnings_recorder.list if "DeprecationWarning" in x._category_name]

    for i in deprecated_warnings:
        i.item = item

    all_deprecated_warnings.extend(deprecated_warnings)


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config=None):
    def clean_duplicated(all_deprecated_warnings):
        cleaned_list = []
        seen = set()

        for warning in all_deprecated_warnings:
            quadruplet = (warning.filename, warning.lineno, warning.category, str(warning.message))

            if quadruplet in seen:
                continue

            seen.add(quadruplet)
            cleaned_list.append(warning)

        return sorted(cleaned_list, key=lambda x: (x.filename, x.lineno))

    def count_appereance(all_deprecated_warnings):
        counted = {}

        for warning in all_deprecated_warnings:
            quadruplet = (warning.filename, warning.lineno, warning.category, str(warning.message))

            if quadruplet in counted:
                counted[quadruplet].count += 1
            else:
                warning.count = 1
                counted[quadruplet] = warning

        return counted.values()

    pwd = os.path.realpath(os.curdir)

    def cut_path(path):
        if path.startswith(pwd):
            path = path[len(pwd) + 1:]
        if "/site-packages/" in path:  # tox install the package in general
            path = path.split("/site-packages/")[1]
        return path

    def format_test_function_location(item):
        return "%s::%s:%s" % (item.location[0], item.location[2], item.location[1])

    yield

    # try to grab tox env name because tox don't give it
    for test in terminalreporter.stats.get("passed", []) + terminalreporter.stats.get("failed", []):
        if ".tox/" in test.location[0]:
            tox_env_name = test.location[0].split(".tox/")[1].split("/")[0]
            output_file_name = "%s-deprecated-warnings.json" % tox_env_name
            break
    else:
        for warning in terminalreporter.stats.get("warnings", []):
            if ".tox/" in warning.fslocation[0]:
                tox_env_name = warning.fslocation[0].split(".tox/")[1].split("/")[0]
                output_file_name = "%s-deprecated-warnings.json" % tox_env_name
                break
        else:
            output_file_name = "deprecated-warnings.json"

    if all_deprecated_warnings:
        print("")
        print("Deprecated warnings summary:")
        print("============================")
        for warning in clean_duplicated(all_deprecated_warnings):
            print("%s\n-> %s:%s %s('%s')" % (format_test_function_location(warning.item), cut_path(warning.filename), warning.lineno, warning.category.__name__, warning.message))

        print("")
        print("All DeprecationWarning errors can be found in the %s file." % output_file_name)

        warnings_as_json = []

        for warning in count_appereance(all_deprecated_warnings):
            serialized_warning = {x: str(getattr(warning.message, x)) for x in dir(warning.message) if not x.startswith("__")}

            serialized_warning.update({
                "count": warning.count,
                "lineno": warning.lineno,
                "category": warning.category.__name__,
                "path": warning.filename,
                "filename": cut_path(warning.filename),
                "test_file": warning.item.location[0],
                "test_lineno": warning.item.location[1],
                "test_name": warning.item.location[2],
                "file_content": open(warning.filename, "r").read(),
                "dependencies": {x.metadata["Name"].lower(): x.metadata["Version"] for x in importlib_metadata.distributions()}
            })

            if "with_traceback" in serialized_warning:
                del serialized_warning["with_traceback"]

            warnings_as_json.append(serialized_warning)

        with open(output_file_name, "w") as f:
            f.write(json.dumps(warnings_as_json, indent=4, sort_keys=True))
            f.write("\n")
    else:
        # nothing, clear file
        with open(output_file_name, "w") as f:
            f.write("")
