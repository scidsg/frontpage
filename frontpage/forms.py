from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import URL, DataRequired, EqualTo, Length, Optional, Regexp, ValidationError

from .models import InvitationCode, User


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long."),
            Regexp(r"(?=.*[A-Za-z])", message="Password must contain letters."),
            Regexp(r"(?=.*[0-9])", message="Password must contain numbers."),
            Regexp(
                r"(?=.*[-!@#$%^&*()_+])",
                message="Password must contain at least one special character (-!@#$%^&*()_+).",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    invite_code = StringField("Invite Code", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already taken. Please choose a different one.")

    def validate_invite_code(self, invite_code):
        code = InvitationCode.query.filter_by(code=invite_code.data, used=False).first()
        if not code:
            raise ValidationError("Invalid or expired invite code.")


class BioForm(FlaskForm):
    bio = TextAreaField("Bio", render_kw={"placeholder": "Tell us something about yourself"})
    submit_bio = SubmitField("Update Bio")


class PasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Current Password"},
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128, message="Password must be at least 8 characters long."),
            Regexp(r"(?=.*[A-Za-z])", message="Password must contain letters."),
            Regexp(r"(?=.*[0-9])", message="Password must contain numbers."),
            Regexp(
                r"(?=.*[-!@#$%^&*()_+])",
                message="Password must contain at least one special character (-!@#$%^&*()_+).",
            ),
        ],
        render_kw={"placeholder": "New Password"},
    )
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match."),
        ],
        render_kw={"placeholder": "Confirm New Password"},
    )
    submit_password = SubmitField("Update Password")


class DisplayNameForm(FlaskForm):
    display_name = StringField(
        "Display Name",
        validators=[Length(max=100)],
        render_kw={"placeholder": "Enter a display name"},
    )
    submit_display_name = SubmitField("Update Display Name")


class TeamPageForm(FlaskForm):
    include_in_team_page = BooleanField("Include in Team Page", default=False)
    submit_team = SubmitField("Update Team Setting")


class CustomUrlForm(FlaskForm):
    custom_url = StringField(
        "Custom URL",
        validators=[Optional(), URL(message="Must be a valid URL.")],
        render_kw={"placeholder": "Enter your custom URL"},
    )
    submit_custom_url = SubmitField("Update Custom URL")


class AvatarForm(FlaskForm):
    avatar = FileField("Avatar", validators=[FileAllowed(["jpg", "png"], "Images only!")])
    submit_avatar = SubmitField("Upload Avatar")
