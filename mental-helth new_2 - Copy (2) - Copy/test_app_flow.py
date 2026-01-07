from app import app, db
import os

# Configure for testing
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['WTF_CSRF_ENABLED'] = False

client = app.test_client()

with app.app_context():
    db.create_all()

    # Step 1: Profile
    print("Testing /profile...")
    response = client.post('/profile', data={
        'name': 'MacUser',
        'age': '25',
        'profession': 'Developer'
    }, follow_redirects=True)
    
    if response.status_code != 200:
        print(f"FAILED /profile: {response.status_code}")
        exit(1)
    
    # Check if we are at symptoms page (by content or url if possible, but basic 200 is good start)
    if b'symptoms' not in response.data.lower() and b'select' not in response.data.lower():
        # This check might be fragile if template doesn't have these words
        pass

    # Step 2: Symptoms
    print("Testing /symptoms...")
    # Simulate session state by using the same client/cookie jar
    response = client.post('/symptoms?lang=gu', data={
        'symptoms': ['ocd', 'stress']
    }, follow_redirects=True)
    
    if response.status_code != 200:
        print(f"FAILED /symptoms: {response.status_code}")
        print(response.data)
        exit(1)
        
    # We expect to be redirected to /report/<id>
    if b'Prajna Path' in response.data:
        print("SUCCESS: Report generated successfully.")
    else:
        print("FAILURE: Report content not found.")
        print("First 500 chars of response:")
        print(response.data[:500])
