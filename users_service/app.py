from flask import Flask, request, jsonify
from db import get_db

app = Flask(__name__)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    email = data.get('email')

    db = get_db()
    with db.cursor() as cursor:
        sql = "INSERT INTO users (email) VALUES (%s)"
        cursor.execute(sql, (email,))
    db.commit()

    return jsonify({'message': 'User created successfully'}), 201


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    db = get_db()
    with db.cursor() as cursor:
        sql = "SELECT * FROM users WHERE user_id = %s"
        cursor.execute(sql, (user_id,))
        user = cursor.fetchone()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(user), 200

if __name__ == '__main__':
    app.run(debug=True, port=5004)