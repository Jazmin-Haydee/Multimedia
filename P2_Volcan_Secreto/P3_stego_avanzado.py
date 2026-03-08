import hashlib, struct, random

def derivar_clave(password: str, longitud: int) -> bytes:
    '''Genera una clave de longitud arbitraria usando SHA-256 en modo
    contador'''
    clave = b''
    contador = 0
    while len(clave) < longitud:
        bloque = hashlib.sha256(password.encode() + struct.pack('<I',
        contador)).digest()
        clave += bloque
        contador += 1
    return clave[:longitud]

def cifrar_xor(mensaje: bytes, password: str) -> bytes:
    clave = derivar_clave(password, len(mensaje))
    return bytes(m ^ k for m, k in zip(mensaje, clave))

def descifrar_xor(cifrado: bytes, password: str) -> bytes:
    return cifrar_xor(cifrado, password)   # XOR es simétrico

def seleccionar_posiciones(total_bytes_imagen: int, seed: int) -> list:
    '''Genera una lista de índices de píxeles aleatorios y únicos, con una semilla para reproducibilidad.'''
    rng = random.Random(seed)
    posiciones = list(range(total_bytes_imagen))
    rng.shuffle(posiciones)
    return posiciones

def semilla_de_password(password: str) -> int:
    '''Convierte la contraseña en un entero para usar como semilla'''
    hash_bytes = hashlib.sha256(password.encode()).digest()
    return int.from_bytes(hash_bytes[:8], 'big')

def embed_secure(src_path, dst_path, mensaje, password):
    header, pixels, width, height, row_size = leer_bmp(src_path)
    msg_bytes  = mensaje.encode('utf-8')
    msg_cifrado= cifrar_xor(msg_bytes, password)
    datos = struct.pack('>I', len(msg_bytes)) + msg_cifrado
    bits = []
    for byte in datos:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    n_bits = len(bits)

    if n_bits > len(pixels):
        raise ValueError('Mensaje demasiado grande')

    seed = semilla_de_password(password)
    # Generar la secuencia completa de posiciones aleatorias una vez
    shuffled_positions = seleccionar_posiciones(len(pixels), seed)
    # Usar solo las primeras n_bits posiciones de esta secuencia para incrustar
    embedding_positions = shuffled_positions[:n_bits]

    pixels_mod = bytearray(pixels)
    for pos, bit in zip(embedding_positions, bits):
        pixels_mod[pos] = (pixels_mod[pos] & 0xFE) | bit
    guardar_bmp(dst_path, header, pixels_mod)
    print(f'[OK] {len(msg_bytes)} bytes cifrados e incrustados en {dst_path}')

def extract_secure(stego_path, password):
    _, pixels, _, _, _ = leer_bmp(stego_path)
    seed = semilla_de_password(password)

    # Regenerar la misma secuencia completa de posiciones aleatorias
    shuffled_positions = seleccionar_posiciones(len(pixels), seed)

    # Extraer los primeros 32 bits para la longitud del mensaje
    # Usando las primeras 32 posiciones de la secuencia aleatoria
    len_bits_positions = shuffled_positions[0:32]
    len_bits = [pixels[p] & 1 for p in len_bits_positions]

    msg_len  = 0
    for b in len_bits:
        msg_len = (msg_len << 1) | b

    # Calcular el número total de bits reales del mensaje (longitud + contenido)
    total_bits_actual = 32 + msg_len * 8

    if total_bits_actual > len(pixels):
        raise ValueError('Extracted message length implies more bits than available in image. Possible corruption or invalid password.')

    # Extraer los bits del mensaje a partir de la posición 32 de la secuencia aleatoria
    msg_bits_positions = shuffled_positions[32:total_bits_actual]
    msg_bits   = [pixels[p] & 1 for p in msg_bits_positions]

    cifrado = bytearray()
    for i in range(0, len(msg_bits), 8):
        byte = 0
        for bit in msg_bits[i:i+8]:
            byte = (byte << 1) | bit
        cifrado.append(byte)
    return descifrar_xor(bytes(cifrado), password).decode('utf-8')

MENSAJE = 'Datos confidenciales de la red 10.0.1.0/24'
CLAVE = 'mi_clave_secreta'

embed_secure('./images/volcan.bmp', 'stego_seguro.bmp', MENSAJE, CLAVE)

resultado = extract_secure('stego_seguro.bmp', CLAVE)
print(f'Clave correcta → "{resultado}"')
assert resultado == MENSAJE

try:
    basura = extract_secure('stego_seguro.bmp', 'claveWrong')
    print(f'Clave incorrecta → "{basura[:30]}..." (texto ilegible esperado)')
except Exception as e:
    print(f'Clave incorrecta → Error: {e}')

def chi_cuadrado_lsb(filepath):
    _, pixels, _, _, _ = leer_bmp(filepath)
    ceros = sum(1 for b in pixels if (b & 1) == 0)
    unos  = len(pixels) - ceros
    esperado = len(pixels) / 2
    chi2 = ((ceros - esperado)**2 + (unos - esperado)**2) / esperado
    print(f'LSBs=0: {ceros}  |  LSBs=1: {unos}  |  χ²= {chi2:.4f}')
    print('  → Valor χ² cercano a 0: distribución uniforme (sin sospecha de LSB secuencial)')
    return chi2

print('=== Imagen original ===')
chi_cuadrado_lsb('./images/volcan.bmp')
print('=== Stego LSB secuencial (Práctica 1) ===')
chi_cuadrado_lsb('./images/stego.bmp')
print('=== Stego LSB aleatorio (Práctica 2) ===')
chi_cuadrado_lsb('stego_seguro.bmp')
