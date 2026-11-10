from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from openfatture.ai.orchestration.workflows.cash_flow_analysis import CashFlowAnalysisWorkflow
from openfatture.ai.orchestration.workflows.compliance_check import ComplianceCheckWorkflow
from openfatture.ai.orchestration.workflows.invoice_creation import InvoiceCreationWorkflow


@pytest.mark.asyncio
async def test_all_workflows_accept_sqlite_checkpointer(tmp_path: Path) -> None:
    provider = MagicMock()
    async with AsyncSqliteSaver.from_conn_string(str(tmp_path / "workflows.sqlite")) as saver:
        with patch(
            "openfatture.ai.orchestration.workflows.cash_flow_analysis.create_provider",
            return_value=provider,
        ):
            workflows = [
                InvoiceCreationWorkflow(provider=provider, checkpointer=saver),
                ComplianceCheckWorkflow(checkpointer=saver),
                CashFlowAnalysisWorkflow(checkpointer=saver),
            ]
        for workflow in workflows:
            assert workflow.graph.checkpointer is saver
            config = {"configurable": {"thread_id": type(workflow).__name__}}
            assert (await workflow.graph.aget_state(config)).values == {}


def test_enabled_checkpointing_requires_explicit_owner() -> None:
    for workflow in (InvoiceCreationWorkflow, ComplianceCheckWorkflow, CashFlowAnalysisWorkflow):
        with pytest.raises(ValueError, match="injected checkpointer"):
            workflow(enable_checkpointing=True)
