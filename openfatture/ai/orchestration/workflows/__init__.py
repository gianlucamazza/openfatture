"""Multi-Agent Workflows using LangGraph.

This module contains workflow definitions that orchestrate multiple AI agents
using LangGraph's state machine framework.

Available workflows:
- InvoiceCreationWorkflow: User input Description Tax Compliance Create
- ComplianceCheckWorkflow: Load invoice Multi-level checks Report
- CashFlowAnalysisWorkflow: Load unpaid Predict Aggregate Insights
- BatchProcessingWorkflow: Parallel execution with rate limiting

Architecture:
Each workflow is a StateGraph that:
1. Defines nodes (agent executions, data operations, human checkpoints)
2. Defines edges (sequential, conditional, parallel)
3. Manages state transitions
4. Handles errors and retries
5. Supports persistent checkpointing

Example:
    >>> from openfatture.ai.orchestration.workflows import InvoiceCreationWorkflow
    >>> workflow = InvoiceCreationWorkflow()
    >>> result = await workflow.execute(user_input="consulenza Python 5h", client_id=123)
    >>> print(f"Invoice created: {result.invoice_id}")
"""


def __getattr__(name: str):
    modules = {
        "CashFlowAnalysisWorkflow": "cash_flow_analysis",
        "create_cash_flow_workflow": "cash_flow_analysis",
        "ComplianceCheckWorkflow": "compliance_check",
        "create_compliance_workflow": "compliance_check",
        "InvoiceCreationWorkflow": "invoice_creation",
        "create_invoice_workflow": "invoice_creation",
    }
    if name in modules:
        from importlib import import_module

        return getattr(import_module(f"{__name__}.{modules[name]}"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Invoice Creation
    "InvoiceCreationWorkflow",
    "create_invoice_workflow",
    # Compliance Check
    "ComplianceCheckWorkflow",
    "create_compliance_workflow",
    # Cash Flow Analysis
    "CashFlowAnalysisWorkflow",
    "create_cash_flow_workflow",
]
