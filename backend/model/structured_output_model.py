from pydantic import BaseModel, Field
from typing import Literal


class StructuredOutput(BaseModel):
    product_id: str = Field(description='The sku_id which was detected')
    agent_name: str = Field(description='The name of the agent which is returning this response')
    metric_name: str = Field(description='The type of anomaly the sku_id shows')
    metric_value: float = Field(description="Specifies how much its deviating from normal")
    severity_score: float = Field(description="Based on loss amount of the product")
    finding_summary: str = Field(description="Give the summary of findings and also recomendation to solve this")
    