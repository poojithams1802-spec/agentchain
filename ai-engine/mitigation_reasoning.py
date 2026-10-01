from typing import Any, Dict


class MitigationReasoning:
    """
    Builds a structured reasoning record from a mitigation
    selector decision.

    This class does not choose or apply controls.
    The MitigationSelector remains responsible for control selection.
    """

    def build_record(
        self,
        *,
        finding: str,
        severity: str,
        evidence: str,
        attack_chain: list[str],
        selected_control: str,
        reason: str,
        priority: float,
        confidence: float,
        retrieved_knowledge: list[str],
        llm_used: bool,
        fallback_used: bool,
    ) -> Dict[str, Any]:
        """
        Build a structured mitigation reasoning record.
        """

        return {
            "finding": finding,
            "severity": severity,
            "evidence": evidence,
            "attack_chain": attack_chain,
            "selected_control": selected_control,
            "reason": reason,
            "priority": priority,
            "confidence": confidence,
            "retrieved_knowledge": retrieved_knowledge,
            "llm_used": llm_used,
            "fallback_used": fallback_used,
        }