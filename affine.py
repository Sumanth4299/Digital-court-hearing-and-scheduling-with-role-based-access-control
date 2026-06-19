import math


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def mod_inverse(a, m):
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return None


def affine_encrypt(text, a=5, b=8):
    m = 256
    if gcd(a, m) != 1:
        raise ValueError(f"Key 'a' ({a}) must be coprime with {m}")
    
    encrypted = []
    for char in text:
        if isinstance(char, int):
            encrypted_val = (a * char + b) % m
        else:
            encrypted_val = (a * ord(char) + b) % m
        encrypted.append(encrypted_val)
    
    return bytes(encrypted)


def affine_decrypt(encrypted_bytes, a=5, b=8):
    m = 256
    if gcd(a, m) != 1:
        raise ValueError(f"Key 'a' ({a}) must be coprime with {m}")
    
    a_inv = mod_inverse(a, m)
    if a_inv is None:
        raise ValueError(f"No modular inverse for key 'a' ({a})")
    
    decrypted = []
    for byte_val in encrypted_bytes:
        if isinstance(byte_val, int):
            decrypted_val = (a_inv * (byte_val - b)) % m
        else:
            decrypted_val = (a_inv * (ord(byte_val) - b)) % m
        decrypted.append(decrypted_val)
    
    return bytes(decrypted)


def encrypt_file_content(content, a=5, b=8):
    if isinstance(content, str):
        content = content.encode('utf-8')
    return affine_encrypt(content, a, b)


def decrypt_file_content(encrypted_content, a=5, b=8):
    return affine_decrypt(encrypted_content, a, b)
