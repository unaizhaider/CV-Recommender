from flask import Flask, jsonify, request, json 

app = Flask(__name__)


@app.route('/users/register', methods=["POST"])
def register():
    #users = mongo.db.users 
    first_name = request.get_json()
    #last_name = request.get_json()['last_name']
   # email = request.get_json()['email']
    #password = bcrypt.generate_password_hash(request.get_json()['password']).decode('utf-8')
   # created = datetime.utcnow()

##    user_id = users.insert({
  #      'first_name': first_name,
   #    'last_name': last_name,
    #    'email': email,
#        'password': password,
##        'created': created 
##    })

    #new_user = users.find_one({'_id': user_id})

    #result = {'email': new_user['email'] + ' registered'}

    return jsonify(first_name)


if __name__ == '__main__':
    app.run(debug=True)