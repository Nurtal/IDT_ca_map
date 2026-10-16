"""PubMed publication types (NCBI E-utilities esummary)."""
from . import http

ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id="


def publication_types(pmids, http_get_json=http.get_json):
    """pmids -> {pmid: [publication types]}; PMIDs unknown to PubMed are left out."""
    result = http_get_json(ESUMMARY + ",".join(pmids)).get("result", {})
    return {uid: result[uid].get("pubtype", []) for uid in result.get("uids", [])}
