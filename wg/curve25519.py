# you can use this if you don't have wg-tools
# otherwise do: wg genkey | tee key.private | wg pubkey > key.public
# this is derived basically exactly from the RFC7748 spec

import base64
import hashlib
import secrets

P = 2**255 - 19
A24 = 121665

def clamp(n):
    n &= ~7
    n &= ~(128 << 8 * 31)
    n |= 64 << 8 * 31
    return n

def x25519(k, u):
    x1 = u
    x2 = 1
    z2 = 0
    x3 = u
    z3 = 1
    swap = 0

    for t in reversed(range(255)):
        k_t = (k >> t) & 1
        swap ^= k_t
        x2, x3 = cswap(swap, x2, x3)
        z2, z3 = cswap(swap, z2, z3)
        swap = k_t

        A = (x2 + z2) % P
        AA = pow(A, 2, P)
        B = (x2 - z2) % P
        BB = pow(B, 2, P)
        E = (AA - BB) % P
        C = (x3 + z3) % P
        D = (x3 - z3) % P
        DA = (D * A) % P
        CB = (C * B) % P
        x3 = pow((DA + CB), 2, P)
        z3 = (x1 * pow((DA - CB), 2, P)) % P
        x2 = (AA * BB) % P
        z2 = (E * (AA + (A24 * E) % P)) % P

    x2, x3 = cswap(swap, x2, x3)
    z2, z3 = cswap(swap, z2, z3)

    return (x2 * pow(z2, P - 2, P)) % P

def cswap(swap, x, y):
    dummy = swap * (x ^ y)
    x ^= dummy
    y ^= dummy
    return (x, y)

def generate_public_key(private_key):
    private_key = clamp(int.from_bytes(private_key, 'little'))
    return x25519(private_key, 9).to_bytes(32, 'little')

def generate_keypair():
    import os
    import base64
    private_key = os.urandom(32)
    public_key = generate_public_key(private_key)
    return base64.b64encode(private_key).decode(), base64.b64encode(public_key).decode()

if __name__ == '__main__':
    private_key, public_key = generate_keypair()
    print("Private key: ", private_key)
    print("Public key:  ", public_key)
