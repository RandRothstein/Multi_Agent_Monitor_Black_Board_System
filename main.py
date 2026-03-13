from orchestrator.supervisor import SupervisorAgent
from detectors.traffic_detector import TrafficDetector
from detectors.conversion_detector import ConversionDetector
from model.evidince_model import Base
from config.db import engine
import asyncio


async def main():

    Base.metadata.create_all(bind=engine)
    supervisor = SupervisorAgent()
    supervisor.user_interface()

    traffic = TrafficDetector()
    convertion = ConversionDetector()

    result = await asyncio.gather(traffic.detect(),convertion.detect())

if __name__ == '__main__':
    asyncio.run(main())
