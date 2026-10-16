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

HUMAN_CONTEXTS = {"human", "in_vitro_human_cells"}
SPECIES_CONTEXTS = HUMAN_CONTEXTS | {"mouse", "rat", "other", "unknown"}

NODE_COLUMNS = ["id", "symbol", "name", "type", "module", "is_seed", "uniprot",
                "synonyms", "function_summary"]
INTERACTION_COLUMNS = ["interaction_id", "source", "target", "type", "directed", "mechanism",
                       "n_sources", "n_pubs", "n_db", "has_human_evidence", "calcium_evidence",
                       "justification", "conflict_with", "evidence_fingerprint"]
EVIDENCE_COLUMNS = ["evidence_id", "interaction_id", "source_kind", "ref", "doi", "year",
                    "first_author", "sentence", "sentence_verified", "species_context"]
