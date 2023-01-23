import os
import json
import pytest
import jsonschema

HOME_DIR = os.getcwd()


def get_json_data(file_name):
    with open(os.path.join(HOME_DIR, "conf", file_name), encoding="utf-8") as json_f:
        json_data = json.load(json_f)
        return json_data


@pytest.mark.dependency(name="json_valid_schema_projects", scope="session")
@pytest.mark.order(0)
def test_json_valid_schema_projects():
    json_data = get_json_data("projects.json")
    json_schema = get_json_data("projects_schema.json")
    try:
        jsonschema.validate(instance=json_data, schema=json_schema)
    except jsonschema.ValidationError:
        pytest.fail("JSON-Schema Validation failed: projects.json "
                    "against schema in the file: projects_schema.json")


@pytest.mark.dependency(name="json_valid_schema_regex", scope="session")
@pytest.mark.order(1)
def test_json_valid_schema_regex():
    json_data = get_json_data("regex.json")
    json_schema = get_json_data("regex_schema.json")
    try:
        jsonschema.validate(instance=json_data, schema=json_schema)
    except jsonschema.ValidationError:
        pytest.fail("JSON-Schema Validation failed: regex.json "
                    "against schema in the file: regex_schema.json")
