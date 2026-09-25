import hashlib, hmac, base64, secrets

def hash_password(password:str)->str:
    salt=secrets.token_bytes(16)
    iterations=310000
    digest=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,iterations)
    return f'pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}'

def verify_password_hash(encoded:str,password:str)->bool:
    try:
        alg,it,salt_b64,dig_b64=encoded.split('$',3)
        if alg!='pbkdf2_sha256': return False
        salt=base64.b64decode(salt_b64); expected=base64.b64decode(dig_b64)
        actual=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,int(it))
        return hmac.compare_digest(actual,expected)
    except Exception:
        return False