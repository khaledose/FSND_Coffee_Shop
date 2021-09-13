import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

# ROUTES
'''
    GET /drinks
        a public endpoint
        contains only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''

@app.route('/drinks')
def get_public_short_drinks():
    try:
        drinks = Drink.query.all()
        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in drinks]
        })
    except:
        abort(500)

'''
    GET /drinks-detail
        requires the 'get:drinks-detail' permission
        contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth(permission='get:drinks-detail')
def get_private_short_drinks(jwt):
    try:
        drinks = Drink.query.all()
        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in drinks]
        })
    except:
        if drinks is None:
            abort(404)
        abort(500)

'''
    POST /drinks
        creates a new row in the drinks table
        requires the 'post:drinks' permission
        contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def post_private_long_drink(jwt):
    try:
        res = request.get_json()
        title = res.get('title', None)
        recipe = str(res.get('recipe', None)).replace('\'','\"')
        drink = Drink(title = title, recipe = recipe)
        drink.insert()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except:
        db.session.rollback()
        abort(500)
    finally:
        db.session.close()

'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        responds with a 404 error if <id> is not found
        updates the corresponding row for <id>
        requires the 'patch:drinks' permission
        contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<drink_id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def patch_private_long_drink(jwt, drink_id):
    try:
        res = request.get_json()
        drink = Drink.query.get(drink_id)
        drink.title = res.get('title', drink.title)
        drink.recipe = str(res.get('recipe', drink.recipe)).replace('\'','\"')
        drink.update()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except:
        db.session.rollback()
        if drink == None:
            abort(404)
        abort(500)
    finally:
        db.session.close()

'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        responds with a 404 error if <id> is not found
        deletes the corresponding row for <id>
        requires the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<drink_id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_private_drink(jwt, drink_id):
    try:
        drink = Drink.query.get(drink_id)
        drink.delete()
        return jsonify({
            'success': True,
            'delete': drink_id
        })
    except:
        db.session.rollback()
        if drink == None:
            abort(404)
        abort(500)
    finally:
        db.session.close()

# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401