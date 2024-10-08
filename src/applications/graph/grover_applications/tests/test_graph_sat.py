import math
import unittest

import matplotlib.pyplot as plt
import networkx
from qiskit.circuit.library import GroverOperator
from qiskit.primitives import Sampler
from qiskit.quantum_info import Statevector
from qiskit_algorithms import AmplificationProblem, Grover

from algorithms.grover import GroverWrapper
from src.applications.graph.grover_applications.graph_oracle import *
from pysat.formula import CNF
from pysat.solvers import Solver
from qiskit.visualization import plot_histogram

from src.utils import get_evolved_state


def adjust_expected_states(expected_states, num_vars, total_qubits):
    """
    Adjusts the expected states to match the total qubits by appending zeros to the end.
    The extra qubits represent the clause output qubits and the final ancilla qubit.
    """
    adjusted_states = []
    for state in expected_states:
        adjusted_state = '0' * (total_qubits - num_vars) + state
        adjusted_states.append(adjusted_state)
    return adjusted_states


def solve_all_cnf_solutions(cnf_formula):
    """
    Finds all solutions to the CNF formula using a SAT solver.

    Args:
        cnf_formula (CNF): The CNF formula to solve.

    Returns:
        list: A list of all satisfying assignments, where each assignment is a list of literals.
    """
    solutions = []
    with Solver(bootstrap_with=cnf_formula) as solver:
        for model in solver.enum_models():
            solutions.append(model)
    return solutions


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_cnf_circuit(self):
        G = networkx.Graph()
        G.add_edges_from([(0, 1), (0, 2), (1, 2)])
        cnf = clique_to_sat(G, 2)
        test_cases = [
            #(cnf, ['10010100', '10010011', '10010010', '10001000', '00010010']),
            (CNF(from_clauses=[[1, -2], [-1, 3], [2]]), ['000', '100', '101', '111', '010']),  # Test Case 1
            (CNF(from_clauses=[[1, 2], [2, 3]]), ['010', '110', '111', '101', '011']),  # Test Case 2
            (CNF(from_clauses=[[1, 2, -3], [-1, 2, -4], [1, 2, 3, 5]]),
             ['01011', '10101', '00000', '00110', '01110', '11111']),  # Test Case 4
        ]
        for cnf_formula, expected_states in test_cases:
            print(f'-----------{cnf_formula}-----------------')
            solutions = solve_all_cnf_solutions(cnf_formula)
            print(f"Solution for CNF3: {solutions}")
            #circuit = cnf_to_quantum_circuit(cnf_formula)
            circuit = cnf_to_quantum_oracle_optimized(cnf_formula)
            total_qubits = circuit.num_qubits
            adjusted_states = adjust_expected_states(expected_states, cnf_formula.nv, total_qubits)
            for state_label in adjusted_states:
                state = Statevector.from_label(state_label)
                get_evolved_state(circuit, state, verbose=True)

    def test_cnf_circuit_optimzed(self):
        G = networkx.Graph()
        G.add_edges_from([(0, 1), (0, 2), (1, 2), (2, 3)])
        cnf = clique_to_sat(G, 3)
        cnf_is = independent_set_to_sat(G)
        test_cases = [
            (CNF(from_clauses=[[1, -2]]), ['00', '01', '10', '11']),  # Test Case 1
            (CNF(from_clauses=[[1, -2], [-1, 3], [2]]), ['000', '100', '101', '111', '010']),  # Test Case 1
            (CNF(from_clauses=[[1, -2], [-1, 3], [-3, 2]]), ['010', '110', '111', '101', '011', '000', '001']),
            # Test Case 2
            (CNF(from_clauses=[[1, 2, -3], [-1, 2, -4], [1, 2, 3, 5]]),
             ['01011', '10101', '00000', '00110', '01110']),  # Test Case 4
            (cnf, ['000100100100', '001000010100', '010000010010', '010000100001', '001001000001', '000101000010',
                   '111111111111']),
            #(cnf, ['0000','0001','0010','0011','0100','0101','0110','0111',
            #'1000','1001','1010','1011','1100','1101','1110','1111'])

        ]
        for cnf_formula, expected_states in test_cases:
            print(f'-----------{cnf_formula}-----------------')
            solutions = solve_all_cnf_solutions(cnf_formula)
            print(f"Solution for CNF3: {solutions}")
            # circuit = cnf_to_quantum_circuit(cnf_formula)
            circuit = cnf_to_quantum_oracle_optimized(cnf_formula)
            print(circuit)
            total_qubits = circuit.num_qubits
            adjusted_states = adjust_expected_states(expected_states, cnf_formula.nv, total_qubits)
            for state_label in adjusted_states:
                state = Statevector.from_label(state_label)
                get_evolved_state(circuit, state, verbose=True)

    def test_cnf_quantum_oracle(self):
        test_cases = [
            (CNF(from_clauses=[[1, -2], [-1, 3], [2]]), ['000', '100', '101', '111', '010'])
        ]
        for cnf_formula, expected_states in test_cases:
            print(f'-----------{cnf_formula}-----------------')
            solutions = solve_all_cnf_solutions(cnf_formula)
            print(f"Solution for CNF3: {solutions}")
            circuit = QuantumCircuit(7)
            circuit.h([0, 1, 2])
            oracle = cnf_to_quantum_oracle(cnf_formula)
            state = Statevector.from_label('0000000')
            state, amplitude = get_evolved_state(circuit, state, verbose=True)
            #state, amplitude = get_evolved_state(oracle, state, verbose=True)
            grover_op = GroverOperator(oracle, reflection_qubits=[0, 1, 2])
            state, amplitude = get_evolved_state(grover_op, state, verbose=True)
            state, amplitude = get_evolved_state(grover_op, state, verbose=True)

    def test_quantum_oracle_cnf(self):
        test_cases = [
            (CNF(from_clauses=[[1, -2], [-1, 3], [2]]), ['111']),  # Test Case 1
            (CNF(from_clauses=[[1, 2], [2, 3]]), ['010', '110', '111', '101', '011']),  # Test Case 2
            (CNF(from_clauses=[[1, 2, -3], [-1, 2, -4], [1, -2, 3, 5]]),
             ['01011', '10101', '00000', '00110', '01110']),  # Test Case 4
        ]
        for cnf_formula, expected_states in test_cases:
            print(f'-----------{cnf_formula}-----------------')
            solutions = solve_all_cnf_solutions(cnf_formula)
            print(f"Solution for CNF3: {solutions}")
            #circuit = cnf_to_quantum_circuit(cnf_formula)
            oracle = cnf_to_quantum_oracle(cnf_formula)
            qc = QuantumCircuit(oracle.num_qubits)
            qc.h(range(cnf_formula.nv))
            grover_op = GroverOperator(oracle, reflection_qubits=list(range(cnf_formula.nv)))
            optimal_num_iterations = math.floor(
                math.pi / (4 * math.asin(math.sqrt(len(expected_states) / 2 ** (cnf_formula.nv)))))
            print(optimal_num_iterations)
            # Apply Grover operator the optimal number of times
            qc.compose(grover_op.power(optimal_num_iterations), inplace=True)
            # Measure all qubits
            qc.measure_all()
            sampler = Sampler()
            result = sampler.run(qc, shots=100000)
            # Access the first quasi-probability distribution
            quasi_dists = result.result().quasi_dists[0]
            print(quasi_dists)
            # Filter out only the first 3 bits for plotting
            filtered_counts = {}
            for state, probability in quasi_dists.items():
                # Take only the first 3 bits of the state
                binary_state = format(state, f'0{grover_op.num_qubits}b')
                num_bits = cnf_formula.nv
                filtered_state = binary_state[-num_bits:]
                if filtered_state in filtered_counts:
                    filtered_counts[filtered_state] += probability
                else:
                    filtered_counts[filtered_state] = probability
            # Plot the histogram for the first 3 bits
            plot_histogram(filtered_counts)
            plt.show()

    def test_clique_cnf(self):
        G = networkx.Graph()
        G.add_edges_from([(0, 1), (0, 2), (1, 2), (2, 3)])
        cnf = clique_to_sat(G, 3)
        solutions = solve_all_cnf_solutions(cnf)
        print(f"Solution for CNF3: {solutions}")
        print(len(cnf.clauses))

    def test_quantum_cnf_grover(self):
        test_cases = [
            (CNF(from_clauses=[[1, 2], [-2], [3, -2]]), ['001', '101']),
            (CNF(from_clauses=[[1, -2], [2, -3]]), ['001']),
            (CNF(from_clauses=[
                [1, -2, 3, -4],  # (x1 OR NOT x2 OR x3 OR NOT x4)
                [-1, 2, 3, 5],  # (NOT x1 OR x2 OR x3 OR x5)
                [2, -3, 4, 6],  # (x2 OR NOT x3 OR x4 OR x6)
                [-1, -4, -5, 7],  # (NOT x1 OR NOT x4 OR NOT x5 OR x7)
            ]), ['10101011', ['1111111']]),
            (CNF(from_clauses=[[1, -2], [-1, 3], [2]]), ['111']),  # Test Case 1

            (CNF(from_clauses=[[1, 2], [2, 3]]), ['010', '110', '111', '101', '011']),  # Test Case 2
            (CNF(from_clauses=[[1, 2, -3], [-1, 2, -4], [1, -2, 3, 5]]),
             ['01011', '10101', '00000', '00110', '01110', '11111']),  # Test Case 4
        ]
        for cnf_formula, expected_states in test_cases:
            print(f'-----------{cnf_formula}-----------------')
            solutions = solve_all_cnf_solutions(cnf_formula)
            print(f"Solution for CNF3: {solutions}")
            oracle = cnf_to_quantum_oracle(cnf_formula)

            def fun(state): return True

            prep = QuantumCircuit(oracle.num_qubits)
            prep.h(range(cnf_formula.nv))
            problem = AmplificationProblem(oracle=oracle,
                                           state_preparation=prep,
                                           objective_qubits=list(range(cnf_formula.nv)),
                                           is_good_state=fun)
            M = len(solutions)
            N = 2 ** cnf_formula.nv
            sin_theta = (2 * math.sqrt(M * (N - M))) / N
            theta = math.asin(sin_theta)
            R = math.ceil(math.acos(math.sqrt(M / N)) / theta)
            print(f"R = {R}")
            optimal_num_iterations = math.floor(
                math.pi / (4 * math.asin(math.sqrt(len(expected_states) / 2 ** (cnf_formula.nv)))))
            grover = Grover(sampler=Sampler(), iterations=2)
            result = grover.amplify(problem)
            print(result)

    def test_grover_wrapper(self):
        # Define the CNF formula
        test_cases = [
            (CNF(from_clauses=[[-1, -2, -3],
                               [1, -2, 3],
                               [1, 2, -3],
                               [1, -2, -3],
                               [-1, 2, 3]]), ['000', '011', '101']),
            (CNF(from_clauses=[[1, -2], [-1, 3], [2]]), ['111']),  # Test Case 1

            (CNF(from_clauses=[[1, 2], [2, 3]]), ['010', '110', '111', '101', '011']),  # Test Case 2
            (CNF(from_clauses=[[1, 2, -3], [-1, 2, -4], [1, -2, 3, 5]]),
             ['01011', '10101', '00000', '00110', '01110', '11111']),
            (CNF(from_clauses=[[1], [-1, -2], [-1, 2, -3], [3, 4]]), ['1001']),
        ]
        # Convert the CNF formula to a quantum oracle
        for cnf_formula, expected_states in test_cases:
            print(f'-----------{cnf_formula}-----------------')
            solutions = solve_all_cnf_solutions(cnf_formula)
            print(f"Solution for CNF3: {solutions}")
            oracle = cnf_to_quantum_oracle(cnf_formula)
            M = len(solutions)
            N = 2 ** cnf_formula.nv
            sin_theta = (2 * math.sqrt(M * (N - M))) / N
            theta = math.asin(sin_theta)
            R = math.floor(math.acos(math.sqrt(M / N)) / theta) + 1
            iterations = R
            optimal_num_iterations = math.floor(
                math.pi / (4 * math.asin(math.sqrt(len(expected_states) / 2 ** cnf_formula.nv)))
            )
            prev = QuantumCircuit(oracle.num_qubits)
            prev.h(range(cnf_formula.nv))

            def fun(state): return True

            grover = GroverWrapper(oracle=oracle,
                                   iterations=iterations,
                                   state_preparation=prev,
                                   objective_qubits=list(range(cnf_formula.nv)),
                                   is_good_state=fun
                                   )
            grover.run(verbose=True)


if __name__ == '__main__':
    unittest.main()
