from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_workflow_nodes():
    """Test getting workflow nodes information"""
    response = client.get("/workflows/basic/nodes")
    assert response.status_code == 200
    nodes = response.json()["nodes"]
    assert "3" in nodes
    assert nodes["3"]["class_type"] == "KSampler" 