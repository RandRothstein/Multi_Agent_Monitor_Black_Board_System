from orchestrator.supervisor import SupervisorAgent
from detectors.traffic_detector import TrafficDetector
from detectors.conversion_detector import ConversionDetector
from model.evidince_model import Base
from config.db import engine
import asyncio
import streamlit as st


async def main():

    Base.metadata.create_all(bind=engine)
    # Run detectors ONLY ONCE when the app starts, not on every button click
    if "detectors_run" not in st.session_state:
        traffic = TrafficDetector()
        conversion = ConversionDetector()
        await asyncio.gather(traffic.detect(), conversion.detect())
        st.session_state.detectors_run = True

    supervisor = SupervisorAgent()
    supervisor.user_interface()

if __name__ == '__main__':
    asyncio.run(main())
