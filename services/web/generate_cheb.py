from math import sqrt
import numpy as np

def generate(N):
    matrix = [[] for i in range(N)]

    for x in range(0, N):
        t0 = 1/sqrt(N)
        t1 = (2*x + 1 - N) * sqrt(3/(N * (N*N - 1)))
        matrix[x].extend([t0, t1])
        for p in range(2, N):
            b1 = 2/p * sqrt((4*p*p-1)/(N*N-p*p))
            b2 = (1-N)/p*sqrt((4*p*p-1)/(N*N-p*p))
            b3 = (1-p)/p*sqrt((2*p+1)/(2*p-3))*sqrt((N*N-(p-1)*(p-1))/(N*N-p*p))
            t_p = (b1*x+b2)*matrix[x][-1] + b3*matrix[x][-2]
            matrix[x].append(t_p)

    for i in range(0, N):
        for j in range(0, i):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    
    #print(str(matrix).replace('[', '{').replace(']', '}'))
    return matrix