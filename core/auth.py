from django.contrib.auth.forms import AuthenticationForm


class CaseInsensitiveAuthForm(AuthenticationForm):
    def clean_username(self):
        return self.cleaned_data.get("username", "").lower().strip()
