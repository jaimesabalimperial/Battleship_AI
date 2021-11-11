import unittest

from battleship.simulation import RandomVsAutomaticSimulation, AutomaticVsAutomaticSimulation

class TestAutomatic(unittest.TestCase):
    def test_10runs(self, num_runs = 100):
        wins = 0
        for _ in range(num_runs):
            #simulation = AutomaticVsAutomaticSimulation()
            simulation = RandomVsAutomaticSimulation()
            jaime_has_won = simulation.run()

            if jaime_has_won:
                wins += 1

        print(f"Jaime has won {wins*100/num_runs}% of the times.")

        assert wins > num_runs/2

