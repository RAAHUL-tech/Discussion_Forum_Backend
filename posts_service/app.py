from flask import Flask, request, jsonify
from db import get_db
from sqs_helper import send_email_to_sqs

app = Flask(__name__)


# Helper function to generate the path for new posts
def generate_materialized_path(parent_post_path, new_post_id):
    return f"{parent_post_path}.{new_post_id}" if parent_post_path else str(new_post_id)


# Route: List posts in a forum or sub-posts based on Materialized Path
@app.route('/forums/<int:forum_id>/posts', methods=['GET'])
def list_posts(forum_id):
    parent_post_id = request.args.get('parent_post_id', None)

    db = get_db()
    with db.cursor() as cursor:
        if parent_post_id:  # If parent_post_id is provided, list sub-posts
            cursor.execute("SELECT path FROM posts WHERE post_id = %s", (parent_post_id,))
            parent_path = cursor.fetchone()['path']
            sql = """
            SELECT p.post_id, p.content, p.created_at, p.path,
                   SUM(CASE WHEN v.vote_type = 'upvote' THEN 1 ELSE 0 END) as upvotes,
                   SUM(CASE WHEN v.vote_type = 'downvote' THEN 1 ELSE 0 END) as downvotes
            FROM posts p
            LEFT JOIN votes v ON p.post_id = v.post_id
            WHERE p.forum_id = %s AND p.path LIKE %s
            GROUP BY p.post_id
            """
            cursor.execute(sql, (forum_id, f"{parent_path}.%"))
        else:  # If no parent_post_id, list top-level posts
            sql = """
            SELECT p.post_id, p.content, p.created_at, p.path,
                   SUM(CASE WHEN v.vote_type = 'upvote' THEN 1 ELSE 0 END) as upvotes,
                   SUM(CASE WHEN v.vote_type = 'downvote' THEN 1 ELSE 0 END) as downvotes
            FROM posts p
            LEFT JOIN votes v ON p.post_id = v.post_id
            WHERE p.forum_id = %s AND p.parent_post_id IS NULL
            GROUP BY p.post_id
            """
            cursor.execute(sql, (forum_id,))

        posts = cursor.fetchall()

    return jsonify(posts), 200


# Route: Create a new post (top-level or sub-post)
@app.route('/forums/<int:forum_id>/posts', methods=['POST'])
def create_post(forum_id):
    data = request.json
    user_id = data['user_id']
    content = data['content']
    parent_post_id = data.get('parent_post_id', None)

    db = get_db()
    with db.cursor() as cursor:
        if parent_post_id:
            cursor.execute("SELECT path FROM posts WHERE post_id = %s", (parent_post_id,))
            parent_path = cursor.fetchone()['path']
        else:
            parent_path = None

        cursor.execute("""
            INSERT INTO posts (forum_id, user_id, content, parent_post_id, path)
            VALUES (%s, %s, %s, %s, '')
        """, (forum_id, user_id, content, parent_post_id))
        new_post_id = cursor.lastrowid

        new_path = generate_materialized_path(parent_path, new_post_id)
        cursor.execute("UPDATE posts SET path = %s WHERE post_id = %s", (new_path, new_post_id))

        cursor.execute("""
            INSERT INTO forum_memberships (forum_id, user_id)
            SELECT %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM forum_memberships WHERE forum_id = %s AND user_id = %s
            )
        """, (forum_id, user_id, forum_id, user_id))

        db.commit()
        # Retrieve all forum members except the user who created the post
        cursor.execute("""
                    SELECT u.email 
                    FROM forum_memberships fm
                    JOIN users u ON fm.user_id = u.user_id
                    WHERE fm.forum_id = %s AND u.user_id != %s
                """, (forum_id, user_id))
        members = cursor.fetchall()

    # Collect all emails
    email_list = [member['email'] for member in members]

    # Send email notification to all forum members
    subject = f"New Post in Forum {forum_id}"
    body = f"A new post has been added to the forum. Check it out!"
    send_email_to_sqs(email_list, subject, body)

    return jsonify({'message': 'Post created successfully'}), 201


if __name__ == '__main__':
    app.run(debug=True, port=5002)
