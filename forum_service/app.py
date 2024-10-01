from flask import Flask, request, jsonify
from db import get_db
from sqs_helper import send_email_to_sqs

app = Flask(__name__)

# Route: Create a new forum
@app.route('/forums', methods=['POST'])
def create_forum():
    data = request.json
    forum_name = data['forum_name']
    description = data['description']
    created_by_user_id = data['created_by_user_id']

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO forums (forum_name, description, created_by_user_id)
            VALUES (%s, %s, %s)
        """, (forum_name, description, created_by_user_id))
        db.commit()
        # Retrieve all user emails to send notifications
        cursor.execute("SELECT email FROM users")
        users = cursor.fetchall()

    # Collect all emails
    email_list = [user['email'] for user in users]

    # Send email to SQS
    subject = f"New Forum Created: {forum_name}"
    body = f"A new forum '{forum_name}' has been created. Check it out!"
    send_email_to_sqs(email_list, subject, body)

    return jsonify({'message': 'Forum created successfully'}), 201

# Route: List all forums and user's memberships
@app.route('/forums', methods=['GET'])
def list_forums():
    user_id = request.args.get('user_id')

    db = get_db()
    with db.cursor() as cursor:
        # Get forums the user is a member of
        cursor.execute("""
            SELECT f.forum_id, f.forum_name, f.description
            FROM forums f
            JOIN forum_memberships fm ON f.forum_id = fm.forum_id
            WHERE fm.user_id = %s
        """, (user_id,))
        member_forums = cursor.fetchall()

        # Get forums not joined by the user
        cursor.execute("""SELECT forum_id, forum_name, description FROM forums 
                       WHERE forum_id NOT IN (SELECT forum_id FROM forum_memberships 
                       WHERE user_id = %s)""", (user_id,))
        available_forums = cursor.fetchall()

    return jsonify({
        'member_forums': member_forums,
        'available_forums': available_forums
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)
