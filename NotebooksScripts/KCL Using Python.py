# Numeric solver using numpy
import numpy as np

def solve_nodes_numeric(RL, RH, V):
    """Solve A x = b for v2,v3,v4 using 1/R notation."""
    invRL = 1.0 / RL
    invRH = 1.0 / RH

    A = np.array([
        [2*invRL + invRH,    -invRL,             0.0],
        [   -invRL,        2*invRL + invRH,    -invRL],
        [    0.0,             -invRL,         invRL + invRH]
    ], dtype=float)

    b = np.array([invRL * V, 0.0, 0.0], dtype=float)

    x = np.linalg.solve(A, b)   # x = [v2, v3, v4]
    return x

# Example usage
if __name__ == "__main__":
    RL = 0.1      # ohms
    RH = 10       # ohms
    V = 1        # volts
    v2, v3, v4 = solve_nodes_numeric(RL, RH, V)
    print("v2 =", v2)
    print("v3 =", v3)
    print("v4 =", v4)
