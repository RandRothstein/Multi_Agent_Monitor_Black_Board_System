from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import extract_sku, supervisor_node, amazonvc_node, summarize

def build_graph():
    workflow = StateGraph(GraphState)

    # Add Nodes
    workflow.add_node("extract_sku", extract_sku)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("amazonvc_node", amazonvc_node)
    workflow.add_node("summarize", summarize)

    # Define Fixed Entry
    workflow.set_entry_point("extract_sku")

    # Supervisor decides: Worker or Summarize
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_node"],
        {
            "amazonvc_node": "amazonvc_node",
            "summarize": "summarize"
        }
    )

    # Workers always return to the Supervisor for the next instruction
    workflow.add_edge("extract_sku", "supervisor")
    workflow.add_edge("amazonvc_node", "supervisor")
    workflow.add_edge("summarize", END)

    return workflow