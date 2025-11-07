# numeric_solve_fixed.py
import numpy as np

# Example numeric values
RL = 0.1      # ohms
RH = 10       # ohms
V1 = 1        # volts

# Coefficient matrix A (3x3)
A = np.array([
    [(2.0/RL + 1.0/RH),  -1.0/RL,             0.0],
    [ -1.0/RL,           (2.0/RL + 1.0/RH),  -1.0/RL],
    [  0.0,              -1.0/RL,            (1.0/RL + 1.0/RH)]
], dtype=float)

# Right-hand side vector b (3x1)
b = np.array([V1/RL, 0.0, 0.0], dtype=float)

# Solve Ax = b
x = np.linalg.solve(A, b)

print("Matrix A:")
print(A)
print("\nRight-hand side b:")
print(b)
print("\nSolution vector x (voltages):")
print(x)
