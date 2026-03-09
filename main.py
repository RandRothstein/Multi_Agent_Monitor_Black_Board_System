from orchestrator.supervisor import SupervisorAgent
from detectors.traffic_detector import TrafficDetector
from model.evidince_model import Base
from config.db import engine

def run():

    detector = TrafficDetector()
    supervisor = SupervisorAgent()


    cases = detector.detect()
    if cases:
        Base.metadata.create_all(bind=engine)
        for case in cases:
            supervisor.run_cases(case)


if __name__ == '__main__':
    run()
