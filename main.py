import numpy as np
import random
import copy
import math
import os



fix_function = False

class Data:
    def __init__(self, A, P, udzial, czyN, u, w, N):
        self.A = copy.deepcopy(A)
        self.P = copy.deepcopy(P)
        self.udzial = np.array(udzial)
        self.czyN = np.array(czyN)
        self.u = np.array(u)
        self.w = np.array(w)
        self.N = np.array(N)


def fix_point(point, data):
    fixed_point = copy.deepcopy(point)
    for i in range(data.A):
        if author_cost(fixed_point[i], i, data) > 0:
            author_publications = [(j, data.w[i][j] / data.u[i][j]) for j in range(data.P)
                                   if data.u[i][j] != 0 and fixed_point[i][j] != 0]
            author_publications.sort(key=lambda x: x[1], reverse=False)
            fixed_point[i][author_publications[0][0]] = 0
            k = 1
            while author_cost(fixed_point[i], i) > 0:
                fixed_point[i][author_publications[k][0]] = 0
                k += 1

    if university_cost(fixed_point, data) > 0:
        publications = [((i, j), data.w[i][j] / data.u[i][j]) for i in range(data.A) for j in range(data.P)
                        if data.u[i][j] != 0 and fixed_point[i][j] != 0]
        publications.sort(key=lambda x: x[1], reverse=False)
        fixed_point[publications[0][0][0]][publications[0][0][1]] = 0
        k = 1
        while university_cost(fixed_point) > 0:
            fixed_point[publications[k][0][0]][publications[k][0][1]] = 0
            k += 1

    return fixed_point


def author_cost(author_publications, author_index, data):
    author_cost = 0
    for j in range(data.P):
        author_cost += author_publications[j] * data.u[author_index][j]
    author_cost -= 4 * data.udzial[author_index]
    return author_cost


def university_cost(point, data):
    university_cost = 0
    for i in range(data.A):
        for j in range(data.P):
            university_cost += point[i][j] * data.u[i][j]

    university_cost -= 3 * data.N

    return university_cost


class Solution:
    def __init__(self, point, data):
        self.point = point
        if fix_function:
            self.fixed_point = fix_point(point)
            self.value = value_function(self.fixed_point, data)
        else:
            self.value = cost_value_function(point, data)


def greedy_pick_point_gen(data):
    point = np.zeros((data.A, data.P), dtype=int)
    for i in range(data.A):
        param_list = [((j, data.w[i][j] / data.u[i][j]) if data.u[i][j] != 0 else (j, 0)) for j in range(0, data.P)]
        param_list.sort(key=lambda x: x[1], reverse=True)
        u_value = data.u[i][param_list[0][0]]
        k = 1
        while u_value <= 4 * data.udzial[i]:
            point[i][param_list[k - 1][0]] = 1
            if k >= data.P-1:
                break
            u_value += data.u[i][param_list[k][0]]
            k += 1

    return point


def random_pick_point_gen(data):
    point = np.zeros((data.A, data.P), dtype=int)
    for i in range(data.A):
        indexes = random.sample(range(data.P), data.P)
        u_value = data.u[i][indexes[0]]
        k = 1
        while u_value <= 4 * data.udzial[i]:
            point[i][indexes[k - 1]] = 1
            u_value += data.u[i][indexes[k]]
            if k >= data.P-1:
                break
            k += 1

    return point


def gen_starting_points(data):
    points = [Solution(np.zeros((data.A, data.P), dtype=int), data), Solution(np.ones((data.A, data.P), dtype=int), data),
              Solution(greedy_pick_point_gen(data), data)]
    for i in range(25):
        points.append(Solution(random_pick_point_gen(data), data))
    return points


def value_function(solution_matrix, data):
    value = 0
    for i in range(data.A):
        for j in range(data.P):
            value += solution_matrix[i][j] * data.w[i][j]

    return value


def cost_value_function(solution_matrix, data, k=250):
    value = 0
    university_cost = 0
    for i in range(data.A):
        author_cost = 0
        for j in range(data.P):
            value += solution_matrix[i][j] * data.w[i][j]
            author_cost += solution_matrix[i][j] * data.u[i][j]
            university_cost += solution_matrix[i][j] * data.u[i][j]
        author_cost -= 4 * data.udzial[i]

        if author_cost > 0:
            value -= k * (1 + author_cost)

    university_cost -= 3 * data.N
    if university_cost > 0:
        value -= k * (1 + university_cost)

    return value


def randomly_change_n_positions(chosen_publications, n, data):
    new_point = copy.deepcopy(chosen_publications.point)
    for k in range(n):
        i = random.randint(0, data.A-1)
        j = random.randint(0, data.P-1)
        new_point[i][j] = 1 if new_point[i][j] == 0 else 1

    return Solution(new_point, data)


def variable_neighborhood_search(init_solution, search_proportion, max_neighborhood_radius, data, file):
    best_solution = init_solution
    count = 0
    iteration = 0
    radius = 1
    stage = 1
    stop = False
    while not stop:
        neighborhood = []
        for i in range(math.floor(search_proportion * data.A * data.P * radius)):
            neighborhood.append(randomly_change_n_positions(best_solution, radius, data))
            count += 1
            if count >= 400:
                exit(0)
                file.write("Stage: " + str(stage) + "K >> best_value: " + str(best_solution.value) + "\n")
                if fix_function:
                    file.write("Found point: " + str(best_solution.point) + "\n"
                               + "Fixed point: " + str(best_solution.fixed_point) + "\n")
                else:
                    file.write("Found point: " + str(best_solution.point) + "\n")
                file.flush()
                if stage == 1000:
                    stop = True
                    break
                stage *= 10

        best_in_neighborhood = max(neighborhood, key=lambda x: x.value)
        if best_in_neighborhood.value > best_solution.value:
            best_solution = best_in_neighborhood
            radius = 1
        else:
            radius += 1
            if radius > max_neighborhood_radius:
                radius = 1
        print("Iteration = ", iteration, "Radius = ", radius , ">> Score ", best_solution.value, "count = ", count)
        iteration += 1

    return best_solution


def main():
    datafiles = os.listdir("data")

    for datafile in datafiles:
        neighborhood_param = 1 / 10
        max_radius = 20

        # update global variables by executing data file
        file = open("results/" + datafile + ".txt", "w+")
        exec(open("data/" + datafile).read())

        N = sum(czyN)

        data = Data(A, P, udzial, czyN, u, w, N)
        # calculation for cost function
        print("File - " + datafile)
        file.write("File - " + datafile + "\n")
        print("Cost function")
        file.write("---Cost function---\n")
        file.flush()
        points = gen_starting_points(data)
        for i, point in enumerate(points):
            print("Calculating point: " + str(i) + " neighborhood param: "
                  + str(neighborhood_param) + " max radius: " + str(max_radius) + " end at: count = " + str(
                1000 * A * P))
            file.write("Calculating point: " + str(i) + " neighborhood param: "
                       + str(neighborhood_param) + " max radius: " + str(max_radius) + "\n")
            file.flush()
            solution = variable_neighborhood_search(point, neighborhood_param, max_radius, data, file)
            file.write("Found point: " + str(solution.point) + "\n")
            file.flush()

        # calculation for fix function
        fix_function = True
        print("File - " + datafile)
        file.write("File - " + datafile + "\n")
        print("Fix function")
        file.write("---Fix function---\n")
        file.flush()
        points = gen_starting_points()
        for i, point in enumerate(points):
            print("Calculating point: " + str(i) + " neighborhood param: "
                  + str(neighborhood_param) + " max radius: " + str(max_radius) + " end at: count = " + str(
                1000 * A * P))
            file.write("Calculating point: " + str(i) + " neighborhood param: "
                       + str(neighborhood_param) + " max radius: " + str(max_radius) + "\n")
            file.flush()
            solution = variable_neighborhood_search(point, neighborhood_param, max_radius, data, file)
            file.write("Found point: " + str(solution.point) + "\n"
                       + "fixed point:" + str(solution.point) + "\n")
            file.flush()
        file.close()

    print("PROGRAM END")


if __name__ == "__main__":
    main()


