from orchestrator.supervisor import SupervisorAgent
from detectors.traffic_detector import TrafficDetector
from model.evidince_model import Base
from config.db import engine

def run():

    supervisor = SupervisorAgent()
    supervisor.user_interface()

if __name__ == '__main__':
    run()
