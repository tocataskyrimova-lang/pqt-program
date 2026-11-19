"""QVCH v4 Studio — the operational API surface (brief 15.1).

The Studio keeps a thin, well-defined API. Its *meaning* changed from v3:

- ``analyze`` shows the StructuredDraft and the claim types CVL extracted;
- ``ingest`` never accepts ``approved`` / ``safe_to_commit`` from the client.
  The MANAS verifier verdict is derived by the system from pipeline validity,
  never from LLM confidence or a client flag. Every write is gated by a valid
  ``AUTHORIZE_WRITE`` Decision Envelope verified through the Gateway;
- ``apply`` runs the Applicability Gate and binds the usage outcome;
- ``maintain`` runs Spanda (viability) and Vinasha (loss of influence);
- retrieval surfaces epistemic labels, confidence components, conflicts and
  the exact revision.

No command or method in this module may bypass MANAS/Gateway for a protected
write (brief 15.2).
"""

from qvch_v4.studio.api import Studio

__all__ = ["Studio"]
