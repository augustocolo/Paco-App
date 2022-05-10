from pulp import *


def solve_session_knapsack(deliveries, capacity):
    item_count = len(deliveries)
    x = pulp.LpVariable.dicts('del', range(item_count), lowBound=0, upBound=1, cat='Integer')

    problem = LpProblem("Knapsack deliveries", LpMaximize)
    problem += lpSum([x[i] * deliveries[i].price for i in range(item_count)]), "Objective: Maximize price"
    problem += lpSum([x[i] * deliveries[i].get_volume() for i in range(item_count)]) <= capacity, "Constraint: Maximum capacity"

    problem.solve()

    max_price = value(problem.objective)

    sol = []

    used_cap = 0
    for i in range(item_count):
        if x[i].value() == 1:
            sol.append(deliveries[i])
            used_cap += deliveries[i].get_volume()

    return sol, max_price, used_cap
