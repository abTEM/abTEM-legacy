import numba as nb
import numpy as np
from numba import jit, prange


@nb.vectorize([nb.complex64(nb.float32), nb.complex128(nb.float64)])
def complex_exponential(x):
    return np.cos(x) + 1.j * np.sin(x)


@nb.vectorize([nb.float32(nb.complex64), nb.float64(nb.complex128)])
def abs2(x):
    return x.real ** 2 + x.imag ** 2


@jit(nopython=True, nogil=True, parallel=True)
def interpolate_radial_functions(array, disc_indices, positions, v, r, dvdr, sampling):
    n = r.shape[0]
    dt = np.log(r[-1] / r[0]) / (n - 1)
    for i in range(positions.shape[0]):
        for j in prange(disc_indices.shape[0]):
            k = round(positions[i, 0] / sampling[0]) + disc_indices[j, 0]
            l = round(positions[i, 1] / sampling[1]) + disc_indices[j, 1]
            # k = position_indices[i, 0] + disc_indices[j, 0]
            # l = position_indices[i, 1] + disc_indices[j, 1]
            if ((k < array.shape[0]) & (l < array.shape[1]) & (k >= 0) & (l >= 0)):
                r_interp = np.sqrt((k * sampling[0] - positions[i, 0]) ** 2 +
                                   (l * sampling[1] - positions[i, 1]) ** 2)
                idx = int(np.floor(np.log(r_interp / r[0] + 1e-7) / dt))
                if (idx < 0):
                    array[k, l] += v[i, 0]
                elif (idx < n - 1):
                    array[k, l] += v[i, idx] + (r_interp - r[idx]) * dvdr[i, idx]


# @jit(nopython=True, nogil=True, parallel=True)
# def window_and_collapse(probes: np.ndarray, S: np.ndarray, corners, coefficients):
#     """
#     Function for collapsing a Prism scattering matrix into a probe wave function.
#
#     Parameters
#     ----------
#     probes : 3d numpy.ndarray
#         The array in which the probe wave functions should be written.
#     S : 3d numpy.ndarray
#         Scattering matrix
#     corners :
#     coefficients :
#     """
#     N, M = S.shape[1:]
#     n, m = probes.shape[1:]
#     for k in prange(len(corners)):
#         i, j = corners[k]
#         ti = n - (N - i)
#         tj = m - (M - j)
#         if (i + n <= N) & (j + m <= M):
#             for l in range(len(coefficients[k])):
#                 probes[k, :] += S[l, i:i + n, j:j + m] * coefficients[k][l]
#
#         elif (i + n <= N) & (j + m > M):
#             for l in range(len(coefficients[k])):
#                 probes[k, :, :-tj] += S[l, i:i + n, j:] * coefficients[k][l]
#                 probes[k, :, -tj:] += S[l, i:i + n, :tj] * coefficients[k][l]
#
#         elif (i + n > N) & (j + m <= M):
#             for l in range(len(coefficients[k])):
#                 probes[k, :-ti, :] += S[l, i:, j:j + m] * coefficients[k][l]
#                 probes[k, -ti:, :] += S[l, :ti, j:j + m] * coefficients[k][l]
#
#         elif (i + n > N) & (j + m > M):
#             for l in range(len(coefficients[k])):
#                 probes[k, :-ti, :-tj] += S[l, i:, j:] * coefficients[k][l]
#                 probes[k, :-ti, -tj:] += S[l, i:, :tj] * coefficients[k][l]
#                 probes[k, -ti:, -tj:] += S[l, :ti, :tj] * coefficients[k][l]
#                 probes[k, -ti:, :-tj] += S[l, :ti, j:] * coefficients[k][l]


@jit(nopython=True, nogil=True, parallel=True, fastmath=True)
def window_and_collapse(probes: np.ndarray, S: np.ndarray, corners, coefficients):
    """
    Function for collapsing a Prism scattering matrix into a probe wave function.

    Parameters
    ----------
    probes : 3d numpy.ndarray
        The array in which the probe wave functions should be written.
    S : 3d numpy.ndarray
        Scattering matrix
    corners :
    coefficients :
    """
    N, M = S.shape[1:]
    for k in prange(probes.shape[0]):
        cx, cy = corners[k]
        for i in prange(probes.shape[1]):
            ii = (cx + i) % N
            for j in prange(probes.shape[2]):
                jj = (cy + j) % M
                #for l in range(coefficients.shape[1]):
                probes[k, i, j] = (S[:, ii, jj] * coefficients[k][:]).sum()