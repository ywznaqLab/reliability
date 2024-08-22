from flask import Flask, request, jsonify, send_from_directory, g, send_from_directory
import subprocess
import sqlite3
import os

app = Flask(__name__)

def get_db(db_name):
    g.pop('_database', None)
    db = getattr(g, '_database', None)
    if db is None:
        db_path = f"{db_name}.db"
        print(f"Using database path: {db_path}")  # 添加这行来调试路径
        if not os.path.exists(db_path):
            db = g._database = sqlite3.connect(db_path, timeout=10)
            db.execute('PRAGMA journal_mode=WAL;')  # 启用 WAL 模式
            init_db(db)
        else:
            db = g._database = sqlite3.connect(db_path, timeout=10)
            db.execute('PRAGMA journal_mode=WAL;')  # 启用 WAL 模式
    return db

def init_db(db):
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS dataflows (
                        id INTEGER PRIMARY KEY,
                        source TEXT NOT NULL,
                        destination TEXT NOT NULL,
                        tcp_udp_port INTEGER NOT NULL,
                        priority INTEGER NOT NULL,
                        cost INTEGER NOT NULL,
                        time_expect TEXT NOT NULL,
                        isWusunFlag INTEGER NOT NULL,
                        isObserve INTEGER NOT NULL
                    )''')
    db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/get_data', methods=['GET'])
def get_data():
    db_name = request.args.get('dbName')
    db = get_db(db_name)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM dataflows")
    rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append({
            'id': row[0],
            'source': row[1],
            'destination': row[2],
            'tcp_udp_port': row[3],
            'priority': row[4],
            'cost': row[5],
            'time_expect': list(map(int, row[6].split(','))),
            'isWusunFlag': row[7],
            'isObserve': row[8]
        })
    return jsonify(data)

@app.route('/add_data', methods=['POST'])
def add_data():
    db_name = request.args.get('dbName')
    db = get_db(db_name)
    data = request.get_json()
    cursor = db.cursor()
    cursor.execute('''INSERT INTO dataflows (source, destination, tcp_udp_port, priority, cost, time_expect, isWusunFlag, isObserve)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                   (data['source'], data['destination'], data['tcp_udp_port'], data['priority'], data['cost'], ','.join(map(str, data['time_expect'])), data['isWusunFlag'], data['isObserve']))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/delete_data', methods=['DELETE'])
def delete_data():
    db_name = request.args.get('dbName')
    flow_id = request.args.get('id')
    db = get_db(db_name)
    cursor = db.cursor()
    cursor.execute("DELETE FROM dataflows WHERE id = ?", (flow_id,))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/merge_databases', methods=['POST'])
def merge_databases():
    try:
        # 打开或创建总数据库
        main_db = get_db('db')
        cursor_main = main_db.cursor()

        print("Clearing the main database...")  # 调试输出

        # 清空 `db` 数据库中的所有数据
        cursor_main.execute("DELETE FROM dataflows")
        main_db.commit()

        print("Starting to merge databases...")  # 调试输出

        # 合并 ./db1 到 ./db8
        new_id = 1  # 初始化新的ID编号
        for i in range(1, 9):
            db_name = f'db{i}'
            db = get_db(db_name)
            cursor = db.cursor()
            cursor.execute("SELECT * FROM dataflows")
            rows = cursor.fetchall()
            
            for row in rows:
                # 确保在插入时重新分配唯一的ID，并且将各个字段转换为合适的类型
                source = str(row[1])
                destination = str(row[2])
                tcp_udp_port = int(row[3])
                priority = int(row[4])
                cost = float(row[5])
                time_expect = ','.join(map(str, map(int, row[6].split(','))))
                isWusunFlag = int(row[7])
                isObserve = int(row[8])

                cursor_main.execute('''INSERT INTO dataflows (id, source, destination, tcp_udp_port, priority, cost, time_expect, isWusunFlag, isObserve)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                    (new_id, source, destination, tcp_udp_port, priority, cost, time_expect, isWusunFlag, isObserve))
                new_id += 1  # 增加ID编号
        
        main_db.commit()
        print("Databases merged successfully.")  # 调试输出

        print("Running connect.py script...")  # 调试输出
        subprocess.run(["python", "./path/connect.py"], check=True)

        return jsonify({'status': 'success'}), 200
    except sqlite3.IntegrityError as e:
        print(f"SQLite integrity error: {e.args[0]}")  # 输出详细的SQLite错误信息
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except sqlite3.Error as e:
        print(f"SQLite error: {e.args[0]}")  # 输出详细的SQLite错误信息
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # 捕获并输出所有其他异常
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_result_data', methods=['GET'])
def get_result_data():
    conn = sqlite3.connect('result_db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT flow_id FROM routeTable")  
    rows = cursor.fetchall()
    conn.close()
    data = [row[0] for row in rows]  # 提取 id 列的数据
    return jsonify(data)

@app.route('/get_route_data', methods=['GET'])
def get_route_data():
    conn = sqlite3.connect('result_db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT flow_id, route FROM routeTable")  # 假设表名为 routeTable
    rows = cursor.fetchall()
    conn.close()
    data = [{"flow_id": row[0], "route": row[1]} for row in rows]
    return jsonify(data)

@app.route('/get_route', methods=['GET'])
def get_route():
    flow_id = request.args.get('flow_id')
    if not flow_id:
        return jsonify({"error": "flow_id is required"}), 400
    
    conn = sqlite3.connect('result_db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT route FROM routeTable WHERE flow_id = ?", (flow_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({"flow_id": flow_id, "route": result[0]})
    else:
        return jsonify({"error": "No route found for the given flow_id"}), 404

@app.route('/')
def serve_index():
    return send_from_directory('.', 'test_new.html')

@app.route('/server.html')
def serve_server():
    return send_from_directory('.', 'server.html')

@app.route('/switch.html')
def serve_switch():
    return send_from_directory('.', 'switch.html')

@app.route('/show.html')
def show():
    return send_from_directory('.', 'show.html')

@app.route('/我的index.html')
def result():
    return send_from_directory('.', '我的index.html')

@app.route('/开始.html', endpoint='start')
def start_simulation():
    return send_from_directory('.', '开始.html')

@app.route('/img/<path:filename>')
def serve_images(filename):
    return send_from_directory('img', filename)

if __name__ == '__main__':
    app.run(debug=True)
