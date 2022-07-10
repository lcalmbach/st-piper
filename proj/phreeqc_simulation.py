
import pandas as pd
import numpy as np
from phreeqpython import PhreeqPython
from pathlib import Path
import os
import streamlit as st


class PhreeqcSimulation():
    def __init__(self, project, therm_db:str):
        dir=Path(os.path.dirname(__file__) + "/database")
        self.sim = PhreeqPython(database=therm_db,database_directory=dir)
        self.project = project
        self.solution_identifiers = []

    def add_solution(self, df: pd.DataFrame, identifiers:dict):
        input = dict(zip(df['solution_master_species'], df['value_numeric']))
        solution = self.sim.add_solution(input)
        self.solution_identifiers.append(identifiers)
        return solution.phases

    def get_solution_num(self):
        return len(self.sim.get_solution_list())
    
    def get_solution(self, index):
        sol = self.sim.get_solution[index]
        return sol.composition

    def get_phase_df(self):
        import numpy as np
        nan = np.nan
        rows = []
        for i in range(0, len(self.sim.get_solution_list())):
            self.solution_identifiers[i].update(self.sim.get_solution(i).phases)
            rows.append(self.solution_identifiers[i])
        df = pd.DataFrame.from_dict(rows, orient='columns')
        return df

