from frontpage import app, db, InvitationCode
import secrets
from datetime import datetime, timedelta


def create_invite_code():
    with app.app_context():
        code = secrets.token_urlsafe(16)
        expiration_date = datetime.utcnow() + timedelta(
            days=365
        )  # Set expiration for 1 year
        new_code = InvitationCode(
            code=code, used=False, expiration_date=expiration_date
        )
        db.session.add(new_code)
        db.session.commit()
        return code


def get_number_of_codes():
    while True:
        try:
            num = input(
                "Enter the number of invite codes to generate (or 'exit' to quit): "
            )
            if num.lower() == "exit":
                return None
            number = int(num)
            if number <= 0:
                raise ValueError
            return number
        except ValueError:
            print("Please enter a valid positive integer or 'exit'.")


if __name__ == "__main__":
    number_of_codes = get_number_of_codes()
    if number_of_codes is not None:
        for _ in range(number_of_codes):
            print(create_invite_code())
