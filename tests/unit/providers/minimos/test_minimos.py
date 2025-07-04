from __future__ import annotations

import json
import os
import shutil

import pytest
from vunnel import result, workspace
from vunnel.providers.minimos import Config, Provider, parser
from vunnel.providers.minimos.parser import Parser


class TestParser:
    @pytest.fixture()
    def mock_raw_data(self, helpers):
        """
        Returns stringified version of the following json

        ---
        """
        data = {
            "apkurl": "{{urlprefix}}/{{reponame}}/{{arch}}/{{pkg.name}}-{{pkg.ver}}.apk",
            "archs": ["x86_64"],
            "reponame": "os",
            "urlprefix": "https://packages.mini.dev",
            "packages": [
                {
                    "pkg": {
                        "name": "binutils",
                        "secfixes": {
                            "2.39-r1": ["CVE-2022-38126"],
                            "2.39-r2": ["CVE-2022-38533"],
                            "2.39-r3": ["CVE-2022-38128"],
                        },
                    },
                },
                {
                    "pkg": {
                        "name": "brotli",
                        "secfixes": {"1.0.9-r0": ["CVE-2020-8927"]},
                    },
                },
                {
                    "pkg": {
                        "name": "busybox",
                        "secfixes": {"1.35.0-r3": ["CVE-2022-28391", "CVE-2022-30065"]},
                    },
                },
                {"pkg": {"name": "coreutils", "secfixes": {"0": ["CVE-2016-2781"]}}},
                {"pkg": {"name": "cups", "secfixes": {"2.4.2-r0": ["CVE-2022-26691"]}}},
                {
                    "pkg": {
                        "name": "dbus",
                        "secfixes": {
                            "1.14.4-r0": [
                                "CVE-2022-42010",
                                "CVE-2022-42011",
                                "CVE-2022-42012",
                            ],
                        },
                    },
                },
                {
                    "pkg": {
                        "name": "apko",
                        "secfixes": {
                            "0": ["CVE-2023-45283", "CVE-2023-45284", "GHSA-jq35-85cj-fj4p"],
                            "0.10.0-r6": ["CVE-2023-39325", "CVE-2023-3978"],
                            "0.7.3-r1": ["CVE-2023-28840", "CVE-2023-28841", "CVE-2023-28842"],
                            "0.8.0-r1": ["CVE-2023-30551"],
                        },
                    },
                },
            ],
        }

        return json.dumps(data)

    @pytest.fixture()
    def mock_parsed_data(self):
        """
        Returns the parsed output generated by AlpineDataProvider._load() for the mock_raw_data

        :return:
        """
        release = "rolling"
        dbtype_data_dict = {
            "apkurl": "{{urlprefix}}/{{reponame}}/{{arch}}/{{pkg.name}}-{{pkg.ver}}.apk",
            "archs": ["x86_64"],
            "reponame": "os",
            "urlprefix": "https://packages.mini.dev",
            "packages": [
                {
                    "pkg": {
                        "name": "binutils",
                        "secfixes": {
                            "2.39-r1": ["CVE-2022-38126"],
                            "2.39-r2": ["CVE-2022-38533"],
                            "2.39-r3": ["CVE-2022-38128"],
                        },
                    },
                },
                {
                    "pkg": {
                        "name": "brotli",
                        "secfixes": {"1.0.9-r0": ["CVE-2020-8927"]},
                    },
                },
                {
                    "pkg": {
                        "name": "busybox",
                        "secfixes": {"1.35.0-r3": ["CVE-2022-28391", "CVE-2022-30065"]},
                    },
                },
                {
                    "pkg": {
                        "name": "coreutils",
                        "secfixes": {"0": ["CVE-2016-2781"]},
                    },
                },
                {
                    "pkg": {
                        "name": "cups",
                        "secfixes": {"2.4.2-r0": ["CVE-2022-26691"]},
                    },
                },
                {
                    "pkg": {
                        "name": "dbus",
                        "secfixes": {
                            "1.14.4-r0": [
                                "CVE-2022-42010",
                                "CVE-2022-42011",
                                "CVE-2022-42012",
                            ],
                        },
                    },
                },
                {
                    "pkg": {
                        "name": "apko",
                        "secfixes": {
                            "0": ["CVE-2023-45283", "CVE-2023-45284", "GHSA-jq35-85cj-fj4p"],
                            "0.10.0-r6": ["CVE-2023-39325", "CVE-2023-3978"],
                            "0.7.3-r1": ["CVE-2023-28840", "CVE-2023-28841", "CVE-2023-28842"],
                            "0.8.0-r1": ["CVE-2023-30551"],
                        },
                    },
                },
            ],
        }
        return release, dbtype_data_dict

    def test_load(self, mock_raw_data, tmpdir):
        p = Parser(
            workspace=workspace.Workspace(tmpdir, "test", create=True),
            url="https://packages.mini.dev/advisories/secdb/security.json",
            namespace="minimos",
        )

        os.makedirs(p.secdb_dir_path, exist_ok=True)
        b = os.path.join(p.secdb_dir_path, "security.json")
        with open(b, "w") as fp:
            fp.write(mock_raw_data)

        counter = 0
        for release, dbtype_data_dict in p._load():
            counter += 1
            assert release == "rolling"
            assert isinstance(dbtype_data_dict, dict)
            assert "packages" in dbtype_data_dict

        assert counter == 1

    def test_normalize(self, mock_parsed_data, tmpdir):
        p = Parser(
            workspace=workspace.Workspace(tmpdir, "test", create=True),
            url="https://packages.mini.dev/advisories/secdb/security.json",
            namespace="minimos",
        )
        release = mock_parsed_data[0]
        dbtype_data_dict = mock_parsed_data[1]

        vuln_records = p._normalize(release, dbtype_data_dict)
        assert len(vuln_records) > 0
        assert all("Vulnerability" in x for x in vuln_records.values())
        assert sorted(vuln_records.keys()) == sorted(
            [
                "CVE-2016-2781",
                "CVE-2020-8927",
                "CVE-2022-26691",
                "CVE-2022-28391",
                "CVE-2022-30065",
                "CVE-2022-38126",
                "CVE-2022-38128",
                "CVE-2022-38533",
                "CVE-2022-42010",
                "CVE-2022-42011",
                "CVE-2022-42012",
                "CVE-2023-28840",
                "CVE-2023-28841",
                "CVE-2023-28842",
                "CVE-2023-30551",
                "CVE-2023-39325",
                "CVE-2023-3978",
                "CVE-2023-45283",
                "CVE-2023-45284",
                "GHSA-jq35-85cj-fj4p",
            ],
        )


def test_provider_schema(helpers, disable_get_requests):
    workspace = helpers.provider_workspace_helper(
        name=Provider.name(),
        input_fixture="test-fixtures/input",
    )
    c = Config()
    c.runtime.result_store = result.StoreStrategy.FLAT_FILE
    p = Provider(root=workspace.root, config=c)

    p.update(None)

    assert workspace.num_result_entries() == 59
    assert workspace.result_schemas_valid(require_entries=True)


def test_provider_via_snapshot(helpers, disable_get_requests, monkeypatch):
    workspace = helpers.provider_workspace_helper(
        name=Provider.name(),
        input_fixture="test-fixtures/input",
    )

    c = Config()
    # keep all of the default values for the result store, but override the strategy
    c.runtime.result_store = result.StoreStrategy.FLAT_FILE
    p = Provider(
        root=workspace.root,
        config=c,
    )

    p.update(None)

    workspace.assert_result_snapshots()
