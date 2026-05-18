import bcrypt

def hash_password(password: str) -> str:
    """পাসওয়ার্ডকে হ্যাশ করে সুরক্ষিত স্ট্রিংয়ে রূপান্তর করে।"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ইউজারের দেওয়া পাসওয়ার্ড আসল হ্যাশের সাথে মিলে কি না তা চেক করে।"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# টেস্ট
hashed = hash_password("12345")
print(f"Hashed: {hashed}")
print(f"Verification: {verify_password('12345', hashed)}")