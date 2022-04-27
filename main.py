import re

from flask import Flask, json, jsonify, make_response, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import insert

from weather import get_weather

app = Flask(__name__)
cors = CORS(app, resources=r'/*')
app.debug = True

# 链接数据库
HOSTNAME = '127.0.0.1'
PORT = 3306
DATABASE = 'weather'
USERNAME = 'root'
PASSWORD = '123'
DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(
    USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


# 设置session
SECRET_KEY = "123456"
db = SQLAlchemy(app)


# 定义用户模型
class User(db.Model):
    __tablename__ = "user"
    username = db.Column(db.String(200), primary_key=True,
                         nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)


# 当天天气数据模型
class Weatherdata(db.Model):
    __tablename__ = "weatherdata"
    hours = db.Column(db.Integer, primary_key=True, nullable=False)
    temperature = db.Column(db.Integer)
    direction = db.Column(db.String(200))
    level = db.Column(db.Integer)
    precipitation = db.Column(db.Integer)
    humidity = db.Column(db.Integer)
    quality = db.Column(db.Integer)


# 14天天气数据模型
class Weatherdata14(db.Model):
    __tablename__ = "weatherdata14"
    date = db.Column(db.Integer, primary_key=True, nullable=False)
    weather = db.Column(db.String(200))
    min = db.Column(db.Integer)
    max = db.Column(db.Integer)
    wind_1 = db.Column(db.String(200))
    wind_2 = db.Column(db.String(200))
    level = db.Column(db.Integer)


db.create_all()


# 登录
@app.route('/login', methods=['POST'])
def login():
    res = {
        "code": 0,
        "msg": "OK",
        "data": {}
    }

    getjson = request.get_json()
    print(getjson)
    username = str(getjson['username'])  # json数据格式
    password = str(getjson['password'])  # json数据格式
    print(username, password)
    item_list = User.query.all()  # 提取数据库数据
    if len(username) >= 16 or len(password) >= 16:
        res['code'] = -2
        res['msg'] = '用户名/密码长度不能超多16位'
        return make_response(res)

    for item in item_list:
        if username in item.username:
            if password in item.password:
                return make_response(res)

    res['code'] = -1
    res['msg'] = "请填写正确的账号密码"
    return make_response(res)


# 注册
@app.route('/registered', methods=['POST'])
def registered():
    res = {
        "code": 0,
        "msg": "OK",
        "data": {}
    }

    getjson = request.get_json()
    username1 = str(getjson.get('username'))  # json数据格式
    password1 = str(getjson.get('password'))  # json数据格式
    if not username1 or not password1:
        res['code'] = -1
        res['msg'] = '账号密码不能为空'
        return make_response(res)
    elif len(username1) >= 16 or len(password1) >= 16:
        res['code'] = -2
        res['msg'] = '用户名/密码长度不能超多16位'
        return make_response(res)
    elif not re.findall(r'^[a-zA-Z0-9]+$', username1):
        res['code'] = -3
        res['msg'] = '用户名存在非法字符'
        return make_response(res)

    user1 = User(username=username1, password=password1)

    db.session.add(user1)
    db.session.commit()
    return make_response(res)


@app.route("/get-weather", methods=['GET'])
def weather():
    res = {
        "code": 0,
        "msg": "OK",
        "data": {}
    }

    (data1, data14) = get_weather()
    for item in data1:
        insert_stmt = insert(Weatherdata).values(
            hours=item[0], temperature=item[1],
            direction=item[2], level=item[3],
            precipitation=item[4], humidity=item[5],
            quality=item[6] if item[6] != '' else 0
        )

        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            temperature=item[1],
            direction=item[2], level=item[3],
            precipitation=item[4], humidity=item[5],
            quality=item[6]
        )

        db.session.execute(on_duplicate_key_stmt)
        db.session.commit()

    for item in data14:
        insert_stmt = insert(Weatherdata14).values(date=item[0], weather=item[1],
                                                   min=item[2], max=item[3],
                                                   wind_1=item[4], wind_2=item[5],
                                                   level=item[6])

        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            date=item[0], weather=item[1],
            min=item[2], max=item[3],
            wind_1=item[4], wind_2=item[5],
            level=item[6]
        )

        db.session.execute(on_duplicate_key_stmt)
        db.session.commit()

    return make_response(res)


if __name__ == '__main__':
    app.run()
