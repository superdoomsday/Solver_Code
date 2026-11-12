# pytest loads this file first. It puts the Solver_Code folder on the import
# path so the tests can "import cw1_solver" from any working directory.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
