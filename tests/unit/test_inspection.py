"""Element tree extraction, reference/contained detection, node cap.

Plan refs: Section 10.1 test_inspection, Section 9.2.7, Section 11.1.
S-02 (iterative walk), S-09 (contained cycles), S-19 (opaque references).
"""

from __future__ import annotations

import json

from fhir_inspector_mcp.core.inspection import (
    build_element_tree,
    extract_contained,
    extract_references,
)
from fhir_inspector_mcp.core.limits import NODE_CAP
from fhir_inspector_mcp.core.parser import parse_resource
from tests import factories


def _parse(data: dict, version: str = "R4"):
    model, issues = parse_resource(json.dumps(data), version)
    assert model is not None, issues
    return model


class TestBuildElementTree:
    def test_patient_tree_has_nodes(self) -> None:
        model = _parse(factories.make_patient())
        nodes, truncated = build_element_tree(model)
        assert len(nodes) > 0
        assert truncated is False

    def test_node_shape(self) -> None:
        model = _parse(factories.make_patient())
        nodes, _ = build_element_tree(model)
        for node in nodes:
            assert "path" in node
            assert "required" in node
            assert "repeated" in node
            assert isinstance(node["required"], bool)
            assert isinstance(node["repeated"], bool)

    def test_include_types_true_adds_type(self) -> None:
        model = _parse(factories.make_patient())
        nodes, _ = build_element_tree(model, include_types=True)
        assert all("type" in node for node in nodes)

    def test_include_types_false_omits_type(self) -> None:
        model = _parse(factories.make_patient())
        nodes, _ = build_element_tree(model, include_types=False)
        assert all("type" not in node for node in nodes)

    def test_paths_are_dotted(self) -> None:
        model = _parse(factories.make_patient())
        nodes, _ = build_element_tree(model)
        paths = {n["path"] for n in nodes}
        assert "name" in paths
        assert any(p.startswith("name") for p in paths)

    def test_max_depth_limits_expansion(self) -> None:
        model = _parse(factories.make_patient())
        shallow, _ = build_element_tree(model, max_depth=1)
        deep, _ = build_element_tree(model, max_depth=5)
        assert len(shallow) <= len(deep)

    def test_node_cap_enforced(self) -> None:
        # Build a resource with many populated fields to approach the node cap.
        entries = [{"resource": factories.make_patient(id=f"p{i}")} for i in range(200)]
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": entries}
        model = _parse(bundle)
        nodes, truncated = build_element_tree(model, max_depth=10)
        assert len(nodes) <= NODE_CAP
        if len(nodes) >= NODE_CAP:
            assert truncated is True

    def test_r5_patient_tree(self) -> None:
        model = _parse(factories.make_patient(), "R5")
        nodes, _ = build_element_tree(model)
        assert len(nodes) > 0


class TestExtractReferences:
    def test_managing_organization_reference(self) -> None:
        model = _parse(factories.resource_with_references())
        refs = extract_references(model)
        assert len(refs) >= 1
        targets = {r["target"] for r in refs}
        assert "Organization/example" in targets

    def test_reference_shape(self) -> None:
        model = _parse(factories.resource_with_references())
        refs = extract_references(model)
        for ref in refs:
            assert "source" in ref
            assert "target" in ref

    def test_references_are_opaque_strings(self) -> None:
        # S-19: references are never dereferenced; they stay as strings.
        model = _parse(factories.resource_with_references())
        refs = extract_references(model)
        assert all(isinstance(r["target"], str) for r in refs)

    def test_no_references_returns_empty(self) -> None:
        model = _parse(factories.minimal("Patient"))
        refs = extract_references(model)
        assert refs == []

    def test_observation_subject_reference(self) -> None:
        model = _parse(factories.make_observation())
        refs = extract_references(model)
        targets = {r["target"] for r in refs}
        assert "Patient/example" in targets


class TestExtractContained:
    def test_contained_extracted(self) -> None:
        model = _parse(factories.resource_with_contained())
        contained = extract_contained(model)
        assert len(contained) >= 1

    def test_no_contained_returns_empty(self) -> None:
        model = _parse(factories.minimal("Patient"))
        contained = extract_contained(model)
        assert contained == []

    def test_self_referential_contained_terminates(self) -> None:
        # S-09: circular contained chains must terminate (visited-set detection).
        model = _parse(factories.self_referential_contained())
        contained = extract_contained(model)
        assert isinstance(contained, list)
