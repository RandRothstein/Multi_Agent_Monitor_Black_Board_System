from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class MetricSignal(BaseModel):
    metric_name: str
    metric_value: Optional[float] = None
    baseline_value: Optional[float] = None
    deviation_pct: Optional[float] = None
    severity: str  # LOW / MEDIUM / HIGH / CRITICAL
    is_anomaly: bool

class StructuredOutput(BaseModel):
    product_id: str
    agent_name: str

    # Multiple signals instead of single metric
    signals: List[MetricSignal]

    # SA-2 intelligence layer
    anomaly_type: str  # suppression / traffic_drop / ppm_risk / ncx_spike / oos / compliance
    risk_score: float  # 0–100

    finding_summary: str
    recommendation: str

    data_sources: List[str] = Field(default_factory=list)