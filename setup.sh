#!/bin/bash

# Create main directory structure
mkdir -p app/features/feature_one/tests
mkdir -p app/features/feature_two/tests
mkdir -p app/features/shared/tests
mkdir -p app/static/{css,js,images}
mkdir -p app/templates/{feature_one,feature_two}
mkdir -p tests/{integration,e2e}

# Create necessary files
touch README.md
touch app/__init__.py
touch app/features/__init__.py
touch app/features/feature_one/__init__.py
touch app/features/feature_one/api.py
touch app/features/feature_one/models.py
touch app/features/feature_one/services.py
touch app/features/feature_one/views.py
touch app/features/feature_one/tests/__init__.py
touch app/features/feature_one/tests/test_api.py
touch app/features/feature_one/tests/test_models.py
touch app/features/feature_one/tests/test_services.py
touch app/features/feature_one/tests/test_views.py

touch app/features/feature_two/__init__.py
touch app/features/feature_two/api.py
touch app/features/feature_two/models.py
touch app/features/feature_two/services.py
touch app/features/feature_two/views.py
touch app/features/feature_two/tests/__init__.py
touch app/features/feature_two/tests/test_api.py
touch app/features/feature_two/tests/test_models.py
touch app/features/feature_two/tests/test_services.py
touch app/features/feature_two/tests/test_views.py

touch app/features/shared/__init__.py
touch app/features/shared/utils.py
touch app/features/shared/tests/__init__.py
touch app/features/shared/tests/test_utils.py

touch app/templates/base.html

touch app.py
touch requirements.txt
touch run.sh
touch tests/__init__.py
touch tests/conftest.py
touch tests/integration/__init__.py
touch tests/integration/test_feature_interactions.py
touch tests/e2e/__init__.py
touch tests/e2e/test_user_journeys.py
touch pytest.ini

# Write content to files
cat > app/__init__.py << 'EOF'
from flask import Flask

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Import and register blueprints for features
    from app.features.feature_one.views import feature_one_bp
    from app.features.feature_two.views import feature_two_bp
    
    app.register_blueprint(feature_one_bp)
    app.register_blueprint(feature_two_bp)
    
    return app
EOF

cat > app/features/feature_one/views.py << 'EOF'
from flask import Blueprint, render_template

feature_one_bp = Blueprint('feature_one', __name__, url_prefix='/feature-one')

@feature_one_bp.route('/')
def index():
    return render_template('feature_one/index.html')
EOF

cat > app/features/feature_two/views.py << 'EOF'
from flask import Blueprint, render_template

feature_two_bp = Blueprint('feature_two', __name__, url_prefix='/feature-two')

@feature_two_bp.route('/')
def index():
    return render_template('feature_two/index.html')
EOF

cat > app/features/feature_one/models.py << 'EOF'
class FeatureOneModel:
    """Data model for feature one."""
    
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
EOF

cat > app/features/feature_one/services.py << 'EOF'
from app.features.feature_one.models import FeatureOneModel

class FeatureOneService:
    """Business logic for feature one."""
    
    def get_items(self):
        """Example method to get feature one items."""
        # In a real app, this might fetch from a database
        return [
            FeatureOneModel(1, "Item 1", "Description for item 1"),
            FeatureOneModel(2, "Item 2", "Description for item 2"),
        ]
EOF

cat > app/features/feature_one/api.py << 'EOF'
from flask import Blueprint, jsonify
from app.features.feature_one.services import FeatureOneService

feature_one_api_bp = Blueprint('feature_one_api', __name__, url_prefix='/api/feature-one')
service = FeatureOneService()

@feature_one_api_bp.route('/')
def get_items():
    items = service.get_items()
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'description': item.description
    } for item in items])
EOF

cat > app/features/shared/utils.py << 'EOF'
def format_date(date_obj, format_str='%Y-%m-%d'):
    """Format a date object to string."""
    return date_obj.strftime(format_str)
    
def validate_input(data, required_fields):
    """Validate that input data contains all required fields."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, "Valid input"
EOF

cat > app/templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Flask Vertical Slice App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <header>
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/feature-one">Feature One</a></li>
                <li><a href="/feature-two">Feature Two</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2025 Vertical Slice Flask App</p>
    </footer>
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
EOF

cat > app/templates/feature_one/index.html << 'EOF'
{% extends "base.html" %}

{% block title %}Feature One{% endblock %}

{% block content %}
<h1>Feature One</h1>
<p>This is the main page for Feature One.</p>
<div id="feature-one-content">
    <!-- Dynamic content will be loaded here -->
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/feature_one.js') }}"></script>
{% endblock %}
EOF

cat > app/templates/feature_two/index.html << 'EOF'
{% extends "base.html" %}

{% block title %}Feature Two{% endblock %}

{% block content %}
<h1>Feature Two</h1>
<p>This is the main page for Feature Two.</p>
<div id="feature-two-content">
    <!-- Dynamic content will be loaded here -->
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/feature_two.js') }}"></script>
{% endblock %}
EOF

cat > app.py << 'EOF'
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
EOF

cat > run.sh << 'EOF'
#!/bin/bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
EOF

cat > requirements.txt << 'EOF'
flask==2.3.3
pytest==7.4.0
pytest-flask==1.2.0
flask-wtf==1.1.1
EOF

cat > tests/conftest.py << 'EOF'
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    yield app

@pytest.fixture
def client(app):
    return app.test_client()
EOF

cat > tests/integration/test_feature_interactions.py << 'EOF'
def test_features_integration(client):
    """Test interactions between features."""
    # Example test that checks if both features are working together
    response = client.get('/')
    assert response.status_code == 200
EOF

cat > tests/e2e/test_user_journeys.py << 'EOF'
def test_complete_user_journey(client):
    """Test a complete user journey through the application."""
    # Visit homepage
    response = client.get('/')
    assert response.status_code == 200
    
    # Navigate to feature one
    response = client.get('/feature-one/')
    assert response.status_code == 200
    
    # Navigate to feature two
    response = client.get('/feature-two/')
    assert response.status_code == 200
EOF

cat > app/features/feature_one/tests/test_services.py << 'EOF'
import pytest
from app.features.feature_one.services import FeatureOneService

def test_get_items():
    service = FeatureOneService()
    items = service.get_items()
    
    assert len(items) == 2
    assert items[0].id == 1
    assert items[0].name == "Item 1"
EOF

cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests app/features
python_files = test_*.py
python_functions = test_*
EOF

cat > README.md << 'EOF'
# Flask Vertical Slice Architecture

This project demonstrates a Flask web application structured using the vertical slice architecture pattern, where code is organized by feature rather than by technical layer.

## Project Structure

Each feature has its own directory containing all the components it needs:
- API endpoints (api.py)
- Data models (models.py)
- Business logic (services.py)
- UI views (views.py)
- Tests for each component

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `./run.sh` or `flask run`

## Testing

Run tests with pytest:
```
pytest
```

## Features

### Feature One
Description of what feature one does.

### Feature Two
Description of what feature two does.
EOF

# Make run.sh executable
chmod +x run.sh

echo "Vertical slice architecture project structure has been created successfully!" 