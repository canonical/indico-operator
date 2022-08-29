import os
import re
import json


def no_color(s):
    return re.sub("\u001b\\[.*?[@-~]", "", s)


with open("./test-result.json", encoding="utf-8") as f:
    result = json.load(f)
    lint_result = result["testenvs"]["lint"]["test"]
    lint_success = True
    lint_output = ""
    for lint_test_result in lint_result:
        if lint_test_result["retcode"] != 0:
            lint_success = False
        if lint_test_result["output"]:
            lint_output += lint_test_result["output"]
    unit_result = result["testenvs"]["unit"]["test"]
    unit_success = unit_result[0]["retcode"] == 0
    unit_output = unit_result[0]["output"]
    coverage_result = result["testenvs"]["coverage-report"]["test"]
    coverage_success = coverage_result[0]["retcode"] == 0
    coverage_output = coverage_result[0]["output"]
    reports = {
        "lint": {"success": lint_success, "output": no_color(lint_output)},
        "unit": {"success": unit_success, "output": no_color(unit_output)},
        "coverage": {"success": coverage_success, "output": no_color(coverage_output)}
    }
    final_report = {
        "sha": os.environ["GITHUB_EVENT_PULL_REQUEST_HEAD_SHA"],
        "number": os.environ["GITHUB_EVENT_NUMBER"],
        "reports": reports
    }
    os.makedirs("report", exist_ok=True)
    with open("report.json", "w+", encoding="utf-8") as o:
        json.dump(final_report, o, indent=2)
