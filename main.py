import asyncio
import streamlit as st
from orchestrator.supervisor import SupervisorAgent
from detectors.traffic_detector import TrafficDetector
from detectors.conversion_detector import ConversionDetector
from model.evidince_model import Base
from config.db import engine

# 1. MUST BE FIRST
st.set_page_config(page_title='Solomon Council', layout='wide')

async def run_detectors():
    traffic = TrafficDetector()
    conversion = ConversionDetector()
    await asyncio.gather(traffic.detect(), conversion.detect())

def main():
    Base.metadata.create_all(bind=engine)
    
    if "detectors_run" not in st.session_state:
        asyncio.run(run_detectors())
        st.session_state.detectors_run = True

    supervisor = SupervisorAgent()
    supervisor.user_interface()

if __name__ == '__main__':
    main()