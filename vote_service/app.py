from flask import Flask, request, jsonify
from db import get_db
from sqs_helper import send_email_to_sqs

app = Flask(__name__)

# Route: Vote on a post
@app.route('/posts/<int:post_id>/vote', methods=['POST'])
def vote_on_post(post_id):
    data = request.json
    user_id = data['user_id']
    vote_type = data['vote_type']

    db = get_db()
    with db.cursor() as cursor:
        # Check if user has already voted
        cursor.execute("SELECT vote_id FROM votes WHERE post_id = %s AND user_id = %s", (post_id, user_id))
        existing_vote = cursor.fetchone()

        if existing_vote:
            # Update existing vote
            cursor.execute("UPDATE votes SET vote_type = %s WHERE vote_id = %s", (vote_type, existing_vote['vote_id']))
        else:
            # Create new vote
            cursor.execute("INSERT INTO votes (post_id, user_id, vote_type) VALUES (%s, %s, %s)", (post_id, user_id, vote_type))

        db.commit()
        # Retrieve the email of the user who created the post
        cursor.execute("""
                    SELECT u.email FROM posts p
                    JOIN users u ON p.user_id = u.user_id
                    WHERE p.post_id = %s
                """, (post_id,))
        post_creator = cursor.fetchone()

    # Send email notification to the post creator
    email_list = [post_creator['email']]
    subject = f"New Vote on Your Post"
    body = f"Your post has received a new vote. Check it out!"
    send_email_to_sqs(email_list, subject, body)

    return jsonify({'message': 'Vote recorded successfully'}), 200

# Route: Remove vote from a post
@app.route('/posts/<int:post_id>/vote', methods=['DELETE'])
def remove_vote(post_id):
    data = request.json
    user_id = data['user_id']

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM votes WHERE post_id = %s AND user_id = %s", (post_id, user_id))
        db.commit()

    return jsonify({'message': 'Vote removed successfully'}), 200

# Route: List votes on a post
@app.route('/posts/<int:post_id>/votes', methods=['GET'])
def list_votes(post_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT user_id, vote_type FROM votes WHERE post_id = %s
        """, (post_id,))
        votes = cursor.fetchall()

    return jsonify(votes), 200

if __name__ == '__main__':
    app.run(debug=True, port=5003)

