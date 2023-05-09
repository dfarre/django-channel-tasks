import pytest

from django.core import management


@pytest.mark.django_db
class AuthenticatedDjangoTestCase:
    username, password = 'Alice', 'Alice'
    db_fixtures = ()

    @pytest.fixture(autouse=True)
    def load_db_fixtures(self):
        if self.db_fixtures:
            management.call_command('loaddata', *self.db_fixtures)

    @pytest.fixture(autouse=True)
    def user_login(self, django_user_model, client):
        self.user = django_user_model.objects.create(username=self.username)
        self.user.set_password(self.password)
        self.user.save()
        self.client = client
        assert self.client.login(username=self.username, password=self.password)
