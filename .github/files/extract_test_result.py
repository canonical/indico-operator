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
    static_result = result["testenvs"]["static"]["test"]
    static_success = static_result[0]["retcode"] == 0
    static_output = static_result[0]["output"]
    coverage_result = result["testenvs"]["coverage-report"]["test"]
    coverage_success = coverage_result[0]["retcode"] == 0
    coverage_output = coverage_result[0]["output"]

    sha = os.environ["GITHUB_EVENT_PULL_REQUEST_HEAD_SHA"]
    reports = []
    if not lint_success:
        reports.append(
            f"Lint checks failed for {sha}\n"
            f"```\n{no_color(lint_output).strip()}\n```"
        )
    if not unit_success:
        reports.append(
            f"Unit tests failed for {sha}\n"
            f"```\n{no_color(unit_output).strip()}\n```"
        )

    reports.append(
        f"Test coverage for {sha}\n"
        f"```\n{no_color(coverage_output).strip()}\n```"
        "Static code analysis report\n"
        f"```\n{no_color(static_output).strip()}\n```"
    )
    
    with open("report.json", "w+", encoding="utf-8") as o:
        json.dump(reports, o, indent=2)
