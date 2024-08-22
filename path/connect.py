import time
from collections import deque
from scapy import *
# from dinic import *
from dicnicNew import *
import sqlite3
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.db')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 从 dataflows 表中读取 observer_FlowList 数据
cursor.execute('SELECT source, destination, tcp_udp_port, priority, cost, time_expect, isWusunFlag, isObserve FROM dataflows')
observer_FlowList = cursor.fetchall()

conn.close()

ipList = {
    "192.168.123.111": ["s9", "s10"],
    "192.168.123.103": ["s6", "s8"],
    "192.168.123.197": ["s2", "s4"],
    "192.168.123.194": ["s5", "s7"],
    "192.168.123.196": ["s1", "s3"]
}

def priority_port(input_port):
    port_Priority = [
        [5440, 49654, 24481, 65535],
        [50622],
        [53298],
        [23],
        [873],
        [4],
        [443],
        [80],
    ]
    mapping = {}
    for i in range(len(port_Priority)):
        for j in range(len(port_Priority[i])):
            mapping[port_Priority[i][j]] = i
    return mapping.get(input_port, -1)

ALPHA = {0: 1.00, 1: 1.01, 2: 1.02, 3: 1.03, 4: 1.04, 5: 1.05, 6: 1.06, 7: 1.07}

background_FlowsList = [
    # 你原来定义的background_FlowsList内容...
]

inputFlowsLists = []
for observer_flow in observer_FlowList:
    inputFlow1 = list(observer_flow)  # 将 tuple 转为 list
    priority = inputFlow1[3]
    
    # 检查 priority 是否在 ALPHA 中
    if priority in ALPHA:
        inputFlow1[4] = inputFlow1[4] * ALPHA[priority]  # 处理 cost
    else:
        inputFlow1[4] = inputFlow1[4] * ALPHA[0]  # 使用默认的 ALPHA[0]
        print(f"Warning: Priority {priority} not found in ALPHA, using default ALPHA[0].")
    
    inputFlow1.append(get_flow_id())
    inputFlowsLists.append(inputFlow1)

for inputflow in background_FlowsList:
    port_kind = [5440]
    for port in port_kind:
        inputFlow1 = inputflow[:]
        inputFlow1.insert(2, port)
        priority = inputFlow1[3]
        
        # 检查 priority 是否在 ALPHA 中
        if priority in ALPHA:
            inputFlow1[4] = inputFlow1[4] * ALPHA[priority]  # 处理 cost
        else:
            inputFlow1[4] = inputFlow1[4] * ALPHA[0]  # 使用默认的 ALPHA[0]
            print(f"Warning: Priority {priority} not found in ALPHA, using default ALPHA[0].")
        
        inputFlow1.append(get_flow_id())
        inputFlowsLists.append(inputFlow1)

flowTableTotal = {"s1": [], "s2": [], "s3": [], "s4": [], "s5": [], "s6": [], "s7": [], "s8": [], "s9": [], "s10": []}
flowTableEnd = {"s1": [], "s2": [], "s3": [], "s4": []}

# 调用 dinic_main 函数
routeTable, cannot_route, node_list, backroute_list = dinic_main(graph, inputFlowsLists)

# 输出并打印 routeTable
print("*" * 26 + "routeTable" + "*" * 26)
print(routeTable)

if len(cannot_route) != 0:
    print("*" * 26 + "connot_route" + "*" * 26)
    print(cannot_route)

# 结果数据库文件路径
result_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'result_db.db')

# 连接到结果数据库
conn_result = sqlite3.connect(result_db_path)
cursor_result = conn_result.cursor()

# 清空 routeTable 表（如果存在）
cursor_result.execute('''
DELETE FROM routeTable
''')
conn_result.commit()

# 创建 routeTable 表（如果不存在）
cursor_result.execute('''
CREATE TABLE IF NOT EXISTS routeTable (
    flow_id INTEGER PRIMARY KEY,
    route TEXT
)
''')
conn_result.commit()

# 插入 routeTable 数据到 result_db.db
for flow_id, route_info in routeTable.items():
    route = ' -> '.join(route_info['route'])  # 将 route 列表转化为字符串
    cursor_result.execute('''
    INSERT OR REPLACE INTO routeTable (flow_id, route)
    VALUES (?, ?)
    ''', (flow_id, route))

conn_result.commit()
conn_result.close()
