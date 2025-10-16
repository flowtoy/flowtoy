from evans.cli import run_flow


def test_realistic_flow_with_http(http_server, monkeypatch, tmp_path):
    # http_server yields a base URL like http://127.0.0.1:XXXXX
    hr_url = f"{http_server}/hr"
    sis_programs_url = f"{http_server}/sis/programs"
    sis_courses_url = f"{http_server}/sis/courses"

    # load the YAML template and fill in the server URLs, then write to tmp file
    tpl_path = tmp_path / "flow_realistic_template.yaml"
    if tpl_path.exists():
        tpl = tpl_path.read_text()
    else:
        from pathlib import Path

        project_tpl = Path(__file__).parent / "flow_realistic_template.yaml"
        tpl = project_tpl.read_text()

    # replace only our {hr_url} placeholders; avoid tpl.format which would
    # eat Jinja {{ }}
    yaml_content = (
        tpl.replace("{hr_url}", hr_url)
        .replace("{sis_programs_url}", sis_programs_url)
        .replace("{sis_courses_url}", sis_courses_url)
    )
    cfg_path = tmp_path / "flow_local_http.yaml"
    cfg_path.write_text(yaml_content)

    monkeypatch.setenv("SHORTNAME", "alice")
    flows, status = run_flow([str(cfg_path)])

    # check results
    ldap = flows.get("ldap_lookup", {}).get("ldap")
    assert ldap["uid"] == "uid-alice"

    jobs = flows.get("hr_lookup", {}).get("jobs")
    assert jobs["jobs"][0] == "job-for-uid-alice"

    programs = flows.get("sis_programs", {}).get("programs")
    assert programs["programs"][0] == "program-for-uid-alice"

    courses = flows.get("sis_courses", {}).get("courses")
    assert courses["courses"][0] == "course-for-uid-alice"

    groups = flows.get("grouper_lookup", {}).get("groups")
    assert groups["groups"][0] == "group-for-uid-alice"
