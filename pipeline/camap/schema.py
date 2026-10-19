"""Data contracts shared by the pipeline (see spec, issue #1)."""

LINK_TYPES = {
    # type: directed?
    "activation": True,
    "inhibition": True,
    "physical_binding": False,
    "phosphorylation": True,
    "ubiquitination": True,
    "translocation/trafficking": True,
    "expression_regulation_up": True,
    "expression_regulation_down": True,
    "coexpression": False,
    "Ca2+_flux": True,
    "unknown_regulation": True,
}

LITERATURE_KINDS = {"pubmed", "pmc"}
DATABASE_KINDS = {"signor", "omnipath", "biogrid", "intact"}
# The researcher's own spreadsheets in data_supp/ (issue #16): a curated row is a summary,
# never a quote, so it carries a curator note instead of a verbatim sentence.
CURATED_KINDS = {"curated"}

HUMAN_CONTEXTS = {"human", "in_vitro_human_cells"}
# "unknown" is deliberately in neither set: a claim of unrecorded species is not animal
# evidence, and the murine-only filter must not hide it (issue #16).
ANIMAL_CONTEXTS = {"mouse", "rat", "other"}
SPECIES_CONTEXTS = HUMAN_CONTEXTS | ANIMAL_CONTEXTS | {"unknown"}

# From the curator's gene catalogue (issue #17). The keys must match
# `annotation_columns` in pipeline/config/supp.json, and CURATED_FIELDS in graph/graph.js
# decides which of them the node panel shows.
CURATED_NODE_FIELDS = ["genecards", "protein_type", "localization", "domains",
                       "ca_functionality", "regulation", "functional_assignment"]
# A record may carry `beyond_calcium: true`: keep this claim although it fails the calcium
# criterion, and say so (user decision of 2026-10-19). It is written by hand, record by record,
# for the biological end of an arm — GSDMD -> F3, STING1 -> GPX4 — that the rule would cut off.
NODE_COLUMNS = ["id", "symbol", "name", "type", "module", "is_seed", "calcium_related", "uniprot",
                "synonyms", "function_summary"] + CURATED_NODE_FIELDS
INTERACTION_COLUMNS = ["interaction_id", "source", "target", "type", "directed", "mechanism",
                       "n_sources", "n_pubs", "n_db", "n_curated", "has_human_evidence", "has_animal_evidence", "calcium_evidence", "beyond_calcium", "string_score",
                       "justification", "conflict_with", "evidence_fingerprint"]
EVIDENCE_COLUMNS = ["evidence_id", "interaction_id", "source_kind", "ref", "cited_pmid", "doi", "year",
                    "first_author", "sentence", "sentence_verified", "species_context",
                    "curator_note", "supp_source"]
