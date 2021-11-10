import unittest

from battleship.simulation import RandomVsAutomaticSimulation

class TestAutomatic(unittest.TestCase):
    def test_10runs(self, num_runs = 10):
        wins = 0
        for _ in range(num_runs):
            automatic_has_won = RandomVsAutomaticSimulation()

            if automatic_has_won:
                wins += 1

        print(f"Automatic player has won {wins} / {num_runs} times.")
        assert wins == num_runs