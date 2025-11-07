import numpy as np

def ladder_matrix_general(R_line, R_load, V, N):
    """Build A and b for N-branch ladder network."""
    A = np.zeros((N, N))
    for i in range(N):
        if i < N - 1:
            A[i, i] = 2 / R_line + 1 / R_load
        else:
            A[i, i] = 1 / R_line + 1 / R_load
        if i > 0:
            A[i, i - 1] = -1 / R_line
        if i < N - 1:
            A[i, i + 1] = -1 / R_line
    b = np.zeros(N)
    b[0] = V / R_line
    return A, b

def solve_ladder(R_line, R_load, V, N):
    A, b = ladder_matrix_general(R_line, R_load, V, N)
    v = np.linalg.solve(A, b)
    return v

# Example usage
R_line = 0.01
R_load = 10
V = 1
N = 6
voltages = solve_ladder(R_line, R_load, V, N)
print("Node voltages (v1...vN):")
print(voltages)
