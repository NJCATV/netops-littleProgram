from flask import jsonify


OK = 0
BAD_REQUEST = 4000
UNAUTHORIZED = 4010
FORBIDDEN = 4030
NOT_FOUND = 4040
CONFLICT = 4090
SERVER_ERROR = 5000


def success(data=None, message="ok", http_status=200):
    return jsonify({"code": OK, "message": message, "data": data}), http_status


def fail(code=BAD_REQUEST, message="bad request", data=None, http_status=400):
    return jsonify({"code": code, "message": message, "data": data}), http_status
