# TestClient — hitting your app without a running server
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# The fixture — why it's not just TestClient(app) on its own

@pytest.fixture
def client():
    test_db: dict = {}
    def get_test_db():
        return test_db
    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()