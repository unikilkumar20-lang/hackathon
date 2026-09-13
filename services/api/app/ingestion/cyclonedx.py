import json
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import unquote
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.errors import ValidationException, UnsupportedInputException


@dataclass
class ParsedComponent:
    bom_ref: str
    name: str
    version: str
    ecosystem: str
    namespace: Optional[str] = None
    canonical_purl: Optional[str] = None
    component_type: str = "library"
    description: Optional[str] = None
    hashes: Dict[str, str] = field(default_factory=dict)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedEdge:
    from_ref: str  # consumer / dependent
    to_ref: str    # dependency
    gate_default: str = "unknown"
    context: Dict[str, Any] = field(default_factory=dict)
    provenance: str = "cyclonedx-manifest"


@dataclass
class ParsedCycloneDX:
    raw_content: Dict[str, Any]
    content_hash: str
    parser_version: str
    topology_status: str  # "complete" | "incomplete" | "degraded"
    warnings: List[str]
    root_ref: Optional[str]
    components: List[ParsedComponent]
    edges: List[ParsedEdge]


def parse_purl(purl: str) -> Tuple[str, Optional[str], str, Optional[str]]:
    """Parse standard package-url string into (ecosystem, namespace, name, version).
    Example: 'pkg:npm/%40scope/pkg-name@1.2.3?qualifiers#subpath'
    """
    if not purl or not purl.startswith("pkg:"):
        return ("generic", None, "unknown", None)

    # Strip scheme
    rest = purl[4:]
    # Strip qualifiers & subpath
    if "#" in rest:
        rest = rest.split("#", 1)[0]
    if "?" in rest:
        rest = rest.split("?", 1)[0]

    parts = rest.split("/", 1)
    ecosystem = parts[0].lower()

    if len(parts) == 1:
        return (ecosystem, None, "unknown", None)

    remainder = parts[1]
    # Check for version after '@'
    version = None
    if "@" in remainder:
        pkg_path, version = remainder.rsplit("@", 1)
        version = unquote(version)
    else:
        pkg_path = remainder

    # Check for namespace in pkg_path
    if "/" in pkg_path:
        ns_parts = pkg_path.rsplit("/", 1)
        namespace = unquote(ns_parts[0])
        name = unquote(ns_parts[1])
    else:
        namespace = None
        name = unquote(pkg_path)

    return (ecosystem, namespace, name, version)


class CycloneDXParser:
    """Deterministic parser and validator for CycloneDX 1.5 & 1.6 JSON format."""

    SUPPORTED_VERSIONS = {"1.5", "1.6"}

    @classmethod
    def parse_raw(
        cls,
        raw_bytes: bytes,
        declared_root_ref: Optional[str] = None,
        strict_dangling: bool = True,
    ) -> ParsedCycloneDX:
        """Parse, validate, and extract dependency graph from CycloneDX JSON payload."""
        # 1. Bounds check on input size
        if len(raw_bytes) > settings.MAX_UPLOAD_BYTES:
            raise ValidationException(
                f"Payload size ({len(raw_bytes)} bytes) exceeds maximum limit of {settings.MAX_UPLOAD_BYTES} bytes."
            )

        # 2. JSON Decoding
        try:
            doc = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise UnsupportedInputException(f"Invalid JSON payload: {e}")

        if not isinstance(doc, dict):
            raise UnsupportedInputException("CycloneDX document root must be a JSON object.")

        content_hash = hashlib.sha256(raw_bytes).hexdigest()

        # 3. Format & Schema Validation
        bom_format = doc.get("bomFormat")
        if bom_format != "CycloneDX":
            raise UnsupportedInputException(
                f"Unsupported BOM format: '{bom_format}'. Expected 'CycloneDX'."
            )

        spec_version = str(doc.get("specVersion", "")).strip()
        if spec_version not in cls.SUPPORTED_VERSIONS:
            raise UnsupportedInputException(
                f"Unsupported CycloneDX specVersion: '{spec_version}'. Supported versions are {sorted(list(cls.SUPPORTED_VERSIONS))}."
            )

        warnings: List[str] = []
        components_map: Dict[str, ParsedComponent] = {}

        # 4. Resolve Root Component from metadata
        metadata = doc.get("metadata", {})
        metadata_comp = metadata.get("component")
        root_ref = None

        if metadata_comp and isinstance(metadata_comp, dict):
            m_ref = metadata_comp.get("bom-ref") or metadata_comp.get("name")
            if m_ref:
                m_name = metadata_comp.get("name", "root-app")
                m_version = metadata_comp.get("version", "0.0.0")
                m_purl = metadata_comp.get("purl")
                m_eco = "generic"
                m_ns = None
                if m_purl:
                    m_eco, m_ns, parsed_name, parsed_ver = parse_purl(m_purl)
                    m_name = parsed_name or m_name
                    m_version = parsed_ver or m_version

                root_comp = ParsedComponent(
                    bom_ref=str(m_ref),
                    name=m_name,
                    version=m_version,
                    ecosystem=m_eco,
                    namespace=m_ns,
                    canonical_purl=m_purl,
                    component_type=metadata_comp.get("type", "application"),
                    description=metadata_comp.get("description"),
                    raw_metadata=metadata_comp,
                )
                components_map[root_comp.bom_ref] = root_comp
                root_ref = root_comp.bom_ref

        if declared_root_ref:
            root_ref = declared_root_ref

        # 5. Extract Components
        raw_components = doc.get("components", [])
        if not isinstance(raw_components, list):
            raise UnsupportedInputException("'components' must be a list in CycloneDX document.")

        if len(raw_components) > settings.MAX_GRAPH_NODES:
            raise ValidationException(
                f"Component count ({len(raw_components)}) exceeds maximum allowed nodes ({settings.MAX_GRAPH_NODES})."
            )

        for comp in raw_components:
            if not isinstance(comp, dict):
                continue
            bom_ref = comp.get("bom-ref")
            name = comp.get("name")
            if not name:
                continue

            if not bom_ref:
                # If bom-ref missing, generate stable fallback from name and version
                bom_ref = f"{name}@{comp.get('version', '0.0.0')}"

            bom_ref = str(bom_ref)
            version = str(comp.get("version", "0.0.0"))
            purl = comp.get("purl")

            ecosystem = "generic"
            namespace = None
            if purl:
                p_eco, p_ns, p_name, p_ver = parse_purl(purl)
                ecosystem = p_eco or ecosystem
                namespace = p_ns
                version = p_ver or version
            else:
                # Infer ecosystem from component group or properties if available
                group = comp.get("group")
                if group:
                    namespace = group

            # Hashes
            hashes_dict = {}
            for h in comp.get("hashes", []):
                if isinstance(h, dict) and "alg" in h and "content" in h:
                    hashes_dict[str(h["alg"])] = str(h["content"])

            parsed_comp = ParsedComponent(
                bom_ref=bom_ref,
                name=name,
                version=version,
                ecosystem=ecosystem,
                namespace=namespace,
                canonical_purl=purl,
                component_type=comp.get("type", "library"),
                description=comp.get("description"),
                hashes=hashes_dict,
                raw_metadata=comp,
            )

            if bom_ref in components_map:
                warnings.append(f"Duplicate component bom-ref detected: '{bom_ref}'. Overwriting prior entry.")
            components_map[bom_ref] = parsed_comp

        # 6. Extract and Validate Dependencies
        raw_dependencies = doc.get("dependencies", [])
        if not isinstance(raw_dependencies, list):
            raise UnsupportedInputException("'dependencies' must be a list in CycloneDX document.")

        edges: List[ParsedEdge] = []
        seen_edges = set()

        for dep_entry in raw_dependencies:
            if not isinstance(dep_entry, dict):
                continue
            from_ref = dep_entry.get("ref")
            if not from_ref:
                continue
            from_ref = str(from_ref)

            # Check if consumer exists in components
            if from_ref not in components_map:
                msg = f"Dependency reference '{from_ref}' is not declared in components or metadata."
                if strict_dangling:
                    raise ValidationException(msg)
                warnings.append(msg)

            depends_on = dep_entry.get("dependsOn", [])
            if not isinstance(depends_on, list):
                continue

            for target_ref in depends_on:
                target_ref = str(target_ref)
                if target_ref not in components_map:
                    msg = f"Dangling dependency reference: '{from_ref}' depends on undeclared '{target_ref}'."
                    if strict_dangling:
                        raise ValidationException(msg)
                    warnings.append(msg)

                edge_key = (from_ref, target_ref)
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)

                if len(edges) >= settings.MAX_GRAPH_EDGES:
                    raise ValidationException(
                        f"Edge count exceeded maximum limit ({settings.MAX_GRAPH_EDGES})."
                    )

                edges.append(
                    ParsedEdge(
                        from_ref=from_ref,
                        to_ref=target_ref,
                        gate_default="unknown",
                        context={"parsed_from": "cyclonedx_dependencies"},
                        provenance="cyclonedx-manifest",
                    )
                )

        # 7. Topology completeness check
        topology_status = "complete"
        if not root_ref:
            topology_status = "incomplete"
            warnings.append(
                "Root application component was not identified in metadata.component. Reachability analysis requires mapping an asset root."
            )
        elif len(edges) == 0 and len(components_map) > 1:
            topology_status = "incomplete"
            warnings.append(
                "Document contains components but zero dependency edges. Graph analysis cannot trace transitive relationships."
            )

        return ParsedCycloneDX(
            raw_content=doc,
            content_hash=content_hash,
            parser_version="1.0.0",
            topology_status=topology_status,
            warnings=warnings,
            root_ref=root_ref,
            components=list(components_map.values()),
            edges=edges,
        )
