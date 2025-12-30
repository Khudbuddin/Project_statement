from models import add_new_user, get_user_by_email

# Example: Extend with more user-specific logic if needed
def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):  # Assuming password_hash is index 3
        return user
    return None

# Test
if __name__ == "__main__":
    # Example: Authenticate
    user = authenticate_user("amit.test@gmail.com", "secure_password_123")
    print(user)