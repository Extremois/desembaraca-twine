"""Verify cryptographic and contractual pairing between candidate binary and corresponding sources.

Records technical binding for the project's corresponding-source delivery review.
Matching receipts and planned URLs alone do not prove source completeness or delivery.
Never promotes or publishes candidates to the active runtime catalog.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

DIGEST = re.compile(r'^[0-9a-f]{64}$')


def valid_digest(value):
    return isinstance(value, str) and DIGEST.fullmatch(value) is not None


def validate_delivery_urls(candidate_url, sources_url):
    if candidate_url is None and sources_url is None:
        return
    parsed = []
    for url in (candidate_url, sources_url):
        if not isinstance(url, str) or any(char.isspace() or ord(char) < 32 for char in url):
            raise ValueError('Both planned delivery URLs must be HTTPS URLs')
        part = urlsplit(url)
        if (part.scheme != 'https' or not part.hostname or not part.path.rsplit('/', 1)[-1]
                or part.username is not None or part.password is not None or part.query or part.fragment):
            raise ValueError('Delivery URLs require HTTPS without credentials, query or fragment')
        parsed.append(part)
    binary, sources = parsed
    if (binary.hostname, binary.port, binary.path.rsplit('/', 1)[0]) != (
            sources.hostname, sources.port, sources.path.rsplit('/', 1)[0]) or binary.path == sources.path:
        raise ValueError('Binary and sources require distinct URLs at the same planned release location')


def file_sha256(path, limit=256 * 1024**2):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Archive must be a regular file: {path}")
    hasher = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            total += len(chunk)
            if total > limit:
                raise ValueError(f"Archive exceeds size limit ({limit} bytes): {path}")
            hasher.update(chunk)
    return hasher.hexdigest(), total


def pair_records(candidate_data, sources_data, candidate_archive=None, sources_archive=None,
                 candidate_url=None, sources_url=None, application_revision=None):
    if not isinstance(candidate_data, dict) or candidate_data.get("kind") != "local-candidate-archive":
        raise ValueError("Invalid candidate receipt: must have kind 'local-candidate-archive'")
    if not isinstance(sources_data, dict) or sources_data.get("kind") != "candidate-source-review-material":
        raise ValueError("Invalid sources receipt: must have kind 'candidate-source-review-material'")

    artifact_id = candidate_data.get("artifact_id")
    if (not isinstance(artifact_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', artifact_id)
            or artifact_id != sources_data.get("artifact_id")):
        raise ValueError(f"Artifact ID mismatch: '{artifact_id}' vs '{sources_data.get('artifact_id')}'")

    candidate_exec = candidate_data.get("executable_sha256", "")
    sources_exec = sources_data.get("executable_sha256", "")
    if not valid_digest(candidate_exec) or candidate_exec != sources_exec:
        raise ValueError(f"Executable SHA-256 mismatch or invalid: candidate={candidate_exec}, sources={sources_exec}")

    candidate_prov = candidate_data.get("provenance_sha256", "")
    sources_prov = sources_data.get("provenance_sha256", "")
    if not valid_digest(candidate_prov) or candidate_prov != sources_prov:
        raise ValueError(f"Provenance SHA-256 mismatch or invalid: candidate={candidate_prov}, sources={sources_prov}")

    cand_sha = candidate_data.get("archive_sha256", "")
    cand_bytes = candidate_data.get("archive_bytes", 0)
    if not valid_digest(cand_sha) or type(cand_bytes) is not int or cand_bytes <= 0:
        raise ValueError("Invalid candidate archive hash or size in receipt")

    src_sha = sources_data.get("archive_sha256", "")
    src_bytes = sources_data.get("archive_bytes", 0)
    if not valid_digest(src_sha) or type(src_bytes) is not int or src_bytes <= 0:
        raise ValueError("Invalid sources archive hash or size in receipt")

    revision = application_revision if application_revision is not None else candidate_data.get('application_revision')
    if revision is not None and (not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision)):
        raise ValueError('Application revision must be a full Git commit hash')
    validate_delivery_urls(candidate_url, sources_url)

    if candidate_archive is not None:
        observed_sha, observed_bytes = file_sha256(candidate_archive)
        if observed_sha != cand_sha or observed_bytes != cand_bytes:
            raise ValueError(f"Candidate archive on disk does not match receipt: {observed_sha} vs {cand_sha}")

    if sources_archive is not None:
        observed_sha, observed_bytes = file_sha256(sources_archive)
        if observed_sha != src_sha or observed_bytes != src_bytes:
            raise ValueError(f"Sources archive on disk does not match receipt: {observed_sha} vs {src_sha}")

    is_glibc = "glibc" in artifact_id
    obligations = {
        "lgpl_2_1_section_6_d": ("Acesso equivalente para download das fontes correspondentes no mesmo endpoint de distribuição binária"
                                 if is_glibc else "Não aplicável diretamente (ambiente sem retenção glibc)"),
        "lgpl_2_1_section_6_a": ("Fontes completas da biblioteca e do programa exportadas permitindo relink modificado comprovado"
                                 if is_glibc else "Reconstrução funcional e independência de compilação comprovadas"),
        "epl_2_0_section_3_1": "Fontes completas do Graphviz acompanhadas de declaração expressa de licença e avisos preservados",
        "offline_notices": "Avisos SOURCE-REFERENCES.txt e textos integrais offline incorporados em ambos os arquivos"
    }

    distribution_status = "unpromoted_pending_authorized_distribution"

    pairing = {
        "schema_version": 1,
        "kind": "corresponding-source-delivery-pairing",
        "artifact_id": artifact_id,
        "application_revision": revision,
        "executable_sha256": candidate_exec,
        "provenance_sha256": candidate_prov,
        "pairing_valid": True,
        "archive_verification": {
            "candidate": candidate_archive is not None,
            "sources": sources_archive is not None
        },
        "candidate": {
            "archive": candidate_data.get("archive", "candidate.zip"),
            "sha256": cand_sha,
            "bytes": cand_bytes,
            "inventory_sha256": candidate_data.get("inventory_sha256"),
            "file_count": candidate_data.get("file_count")
        },
        "sources": {
            "archive": sources_data.get("archive", "sources.tar.gz"),
            "sha256": src_sha,
            "bytes": src_bytes,
            "file_count": sources_data.get("file_count"),
            "sdk_files": sources_data.get("sdk_files")
        },
        "obligations": obligations,
        "delivery_binding": {
            "status": distribution_status,
            "candidate_distribution_url": candidate_url,
            "sources_distribution_url": sources_url,
            "active_catalog_promoted": False
        }
    }
    return pairing


def verify_pairing(candidate_receipt_path, sources_receipt_path, candidate_archive_path=None,
                   sources_archive_path=None, candidate_url=None, sources_url=None,
                   application_revision=None):
    with Path(candidate_receipt_path).open("r", encoding="utf-8") as stream:
        cand_data = json.load(stream)
    with Path(sources_receipt_path).open("r", encoding="utf-8") as stream:
        src_data = json.load(stream)
    return pair_records(cand_data, src_data, candidate_archive=candidate_archive_path,
                        sources_archive=sources_archive_path, candidate_url=candidate_url,
                        sources_url=sources_url, application_revision=application_revision)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-receipt", type=Path, required=True, help="Path to candidate.json")
    parser.add_argument("--sources-receipt", type=Path, required=True, help="Path to sources.json")
    parser.add_argument("--candidate-archive", type=Path, default=None, help="Optional path to candidate.zip")
    parser.add_argument("--sources-archive", type=Path, default=None, help="Optional path to sources.tar.gz")
    parser.add_argument("--candidate-url", type=str, default=None, help="Planned HTTPS URL for candidate binary")
    parser.add_argument("--sources-url", type=str, default=None, help="Planned HTTPS URL for corresponding sources")
    parser.add_argument("--application-revision", type=str, default=None, help="Git application commit revision")
    parser.add_argument("--output", type=Path, required=True, help="Output path for pairing.json")
    args = parser.parse_args()

    try:
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError(f"Output pairing receipt already exists: {args.output}")
        result = verify_pairing(
            args.candidate_receipt,
            args.sources_receipt,
            candidate_archive_path=args.candidate_archive,
            sources_archive_path=args.sources_archive,
            candidate_url=args.candidate_url,
            sources_url=args.sources_url,
            application_revision=args.application_revision
        )
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Source pairing verification failed ({type(exc).__name__}): {exc}\n")


if __name__ == "__main__":
    main()
