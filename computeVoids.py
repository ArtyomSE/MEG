import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import pairwise_distances

def search_node_cliques(adj_matrix, i, depth, cliques, curr_clique):
    for j in range(i + 1, adj_matrix.shape[0]):
        if adj_matrix[i, j] == 1:
            next_node_found = True
            for node in curr_clique[:-1]:
                if adj_matrix[j, node] == 0:
                    next_node_found = False

            if next_node_found == True:
                if depth == 1:
                    cliques += [tuple(curr_clique + [j])]
                else:
                    cliques = search_node_cliques(
                        adj_matrix, j, depth - 1, cliques, curr_clique + [j]
                    )
    return cliques


def search_cliques(adj_matrix, ord):
    cliques = []
    for i in range(adj_matrix.shape[0]):
        node_cliques = search_node_cliques(adj_matrix, i, ord - 1, [], [i])
        if len(node_cliques) > 0:
            cliques += node_cliques
    return cliques


def computeVoids(data, radii):
    dist_matrix = pairwise_distances(data)
    filtration = [[tuple([i]) for i in range(dist_matrix.shape[0])]]

    # 1. Building filtration:
    for radius in radii:
        adj_matrix = np.zeros((dist_matrix.shape[0], dist_matrix.shape[0]))
        adj_matrix[dist_matrix[:, :] <= 2 * radius] = 1
        adj_matrix -= np.eye(adj_matrix.shape[0])

        VR_complex = []
        for ord in range(2, 5): # 4 or 5
            cliques = search_cliques(adj_matrix, ord)
            if len(cliques) > 0:
                VR_complex += cliques
        filtration.append(VR_complex)

    for i in range(1, len(filtration)):
        for j in range(i):
            VR_complex_size = len(filtration[i])
            for k in range(VR_complex_size):
                if filtration[i][VR_complex_size - k - 1] in filtration[j]:
                    filtration[i].pop(VR_complex_size - k - 1)

    # 2. Building boundary matrix:
    simplices = [simplex for VR_complex in filtration for simplex in VR_complex]

    VR_complexes_sizes = np.array([len(VR_complex) for VR_complex in filtration])
    boundary_matrix = np.zeros((len(simplices), len(simplices)))

    for i in range(len(filtration)):
        for j in range(i, len(filtration)):
            for p in range(len(filtration[i])):
                for q in range(len(filtration[j])):
                    face = set(filtration[i][p])
                    simplex = set(filtration[j][q])
                    if len(simplex) - len(face) == 1 and simplex.intersection(face) == face:
                        boundary_matrix[
                            np.sum(VR_complexes_sizes[:i]) + p, np.sum(VR_complexes_sizes[:j]) + q
                        ] = 1

    boundary_matrix = boundary_matrix.astype(int)

    # 3. Computing Smith normal from of boundary matrix (hole calculation):
    hole_boundaries = [[simplices[i]] for i in range(len(simplices))]

    for j in range(boundary_matrix.shape[1]):
        last_one_in_col_is_first_in_raw = False

        while last_one_in_col_is_first_in_raw == False:
            try:
                last_one_in_col_index = np.where(boundary_matrix[:, j] == 1)[0][-1]
            except IndexError:
                break
            first_one_in_row_index = np.where(boundary_matrix[last_one_in_col_index, :] == 1)[0][0]

            if first_one_in_row_index == j:
                last_one_in_col_is_first_in_raw = True
            else:
                boundary_matrix[:, j] += boundary_matrix[:, first_one_in_row_index]
                boundary_matrix[:, j] %= 2
                hole_boundaries[j].append(simplices[first_one_in_row_index])

    # 4. Extracting boundaries of holes:
    holes = [
        hole_boundaries[hole_index] for hole_index in np.where(np.sum(boundary_matrix, axis=0) == 0)[0]
    ]
    return holes
