import copy


class Ship:
    def __init__(self, name, hitpoints, matrix):
        self.name = name
        self.hitpoints = hitpoints
        self.matrix = matrix
        self.is_horizontal = True

    def __copy__(self):
        return Ship(self.name, self.hitpoints, copy.deepcopy(self.matrix))

    def rotate(self):
        if self.is_horizontal:
            self.matrix.reverse()
            self.transpose_matrix()
        else:
            self.transpose_matrix()
            self.matrix.reverse()
        self.is_horizontal = not self.is_horizontal

    def transpose_matrix(self):
        for i in range(len(self.matrix)):
            for j in range(i):
                self.matrix[i][j], self.matrix[j][i] = self.matrix[j][i], self.matrix[i][j]

