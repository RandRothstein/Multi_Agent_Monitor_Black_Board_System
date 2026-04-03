import operator
from typing import Annotated, List, Dict, Optional, TypedDict

class GraphState(TypedDict):
    # Metadata
    session_id: str
    user_query: str
    sku: Optional[str]
    
    # Internal Logic
    cases: List[Dict]
    # Annotated with operator.add allows agents to "talk" by adding to this list
    findings: Annotated[List[Dict], operator.add] 
    history: List[Dict]
    next_node: str
    iterations: int