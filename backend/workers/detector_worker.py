import asyncio
from detectors.traffic_detector import TrafficDetector
from detectors.conversion_detector import ConversionDetector

async def run():
    await asyncio.gather(
        TrafficDetector().detect(),
        ConversionDetector().detect()
    )

if __name__ == "__main__":
    asyncio.run(run())