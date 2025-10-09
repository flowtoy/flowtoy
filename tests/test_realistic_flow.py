import os

from flow.cli import run_flow


def test_realistic_flow(monkeypatch):
    monkeypatch.setenv("SHORTNAME", "alice")
    flows, status = run_flow(["tests/flow_realistic.yaml"])

    # assert ldap lookup returned expected fields
    ldap = flows.get("ldap_lookup", {}).get("ldap")
    assert ldap["uid"] == "uid-alice"
    assert "email" in ldap

    # hr jobs
    jobs = flows.get("hr_lookup", {}).get("jobs")
    assert (
        jobs["jobs"][0] == "job-for-uid-alice" or jobs["jobs"][0] == "job-for-uid-alice"
    )

    # sis programs and courses
    programs = flows.get("sis_programs", {}).get("programs")
    assert programs["programs"][0] == "program-for-uid-alice"
    courses = flows.get("sis_courses", {}).get("courses")
    assert courses["courses"][0] == "course-for-uid-alice"

    # grouper groups
    groups = flows.get("grouper_lookup", {}).get("groups")
    assert groups["groups"][0] == "group-for-uid-alice"
