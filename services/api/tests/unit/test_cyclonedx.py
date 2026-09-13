import json
import pytest
from app.ingestion.cyclonedx import CycloneDXParser, parse_purl
from app.core.errors import ValidationException, UnsupportedInputException


def test_parse_purl():
    eco, ns, name, ver = parse_purl("pkg:npm/%40scope/my-pkg@1.2.3")
    assert eco == "npm"
    assert ns == "@scope"
    assert name == "my-pkg"
    assert ver == "1.2.3"

    eco, ns, name, ver = parse_purl("pkg:pypi/requests@2.31.0")
    assert eco == "pypi"
    assert ns is None
    assert name == "requests"
    assert ver == "2.31.0"

    eco, ns, name, ver = parse_purl("invalid-purl")
    assert eco == "generic"


def test_valid_cyclonedx_parsing():
    valid_payload = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "metadata": {
            "component": {
                "bom-ref": "root-app",
                "name": "root-app",
                "version": "1.0.0",
                "type": "application",
            }
        },
        "components": [
            {
                "bom-ref": "lib-a@1.0.0",
                "name": "lib-a",
                "version": "1.0.0",
                "purl": "pkg:npm/lib-a@1.0.0",
            },
            {
                "bom-ref": "lib-b@2.0.0",
                "name": "lib-b",
                "version": "2.0.0",
                "purl": "pkg:npm/lib-b@2.0.0",
            },
        ],
        "dependencies": [
            {
                "ref": "root-app",
                "dependsOn": ["lib-a@1.0.0"],
            },
            {
                "ref": "lib-a@1.0.0",
                "dependsOn": ["lib-b@2.0.0"],
            },
        ],
    }

    raw_bytes = json.dumps(valid_payload).encode("utf-8")
    parsed = CycloneDXParser.parse_raw(raw_bytes, strict_dangling=True)

    assert parsed.topology_status == "complete"
    assert parsed.root_ref == "root-app"
    assert len(parsed.components) == 3  # root-app + 2 libs
    assert len(parsed.edges) == 2
    assert parsed.edges[0].from_ref == "root-app"
    assert parsed.edges[0].to_ref == "lib-a@1.0.0"


def test_dangling_reference_rejection():
    dangling_payload = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "components": [
            {"bom-ref": "pkg-a", "name": "pkg-a", "version": "1.0.0"}
        ],
        "dependencies": [
            {"ref": "pkg-a", "dependsOn": ["ghost-pkg"]}
        ],
    }

    raw_bytes = json.dumps(dangling_payload).encode("utf-8")
    with pytest.raises(ValidationException) as exc:
        CycloneDXParser.parse_raw(raw_bytes, strict_dangling=True)
    assert "Dangling dependency reference" in str(exc.value.message)


def test_invalid_bom_format():
    invalid_format = {"bomFormat": "Spdx", "specVersion": "2.2"}
    raw_bytes = json.dumps(invalid_format).encode("utf-8")
    with pytest.raises(UnsupportedInputException):
        CycloneDXParser.parse_raw(raw_bytes)


def test_malformed_json():
    with pytest.raises(UnsupportedInputException):
        CycloneDXParser.parse_raw(b"not-json{{{")
