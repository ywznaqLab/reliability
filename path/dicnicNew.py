# -*- coding: utf-8 -*-#
# Description: Dinic 算法求解最大流问题
import numpy as np
import sys
import copy
import hashlib
import math
from decimal import Decimal
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt
import random
import statistics
import numpy as np

class Node:
	def __init__(self, name, arc_dict, timedelay, widthband):
		self.name = name
		self.arc_dict = arc_dict
		self.timedelay = timedelay
		self.widthband = widthband



graph = [
	["1",["s1"],[10000],[500],[0]],["2", ["s1"], [10000],[500],[0]],
	["5", ["s2"], [10000],[500],[0]],["6", ["s2"], [10000],[500],[0]],
	["3", ["s3"], [10000],[500],[0]],["4", ["s3"], [10000],[500],[0]],
	["7", ["s4"], [10000],[500],[0]],["8", ["s4"], [10000],[500],[0]],
	["s1", ["1","2","s5","s6"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s2", ["5","6","s5","s6"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s3", ["3","4","s7","s8"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s4", ["7","8","s7","s8"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s5", ["s1","s2","s9","s10"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s6", ["s1","s2","s9","s10"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s7", ["s3","s4","s9","s10"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s8", ["s3","s4","s9","s10"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s9", ["s5","s6","s7","s8"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]],
	["s10", ["s5","s6","s7","s8"], [10000,10000,10000,10000],[500,500,500,500],[0,0,0,0]]
	]

PORT_TRANS = {
	"s1": {"server1": 180, "server2": 156, "s5": 132, "s6": 148 },
	"s2": {"server5": 140, "server6": 156, "s5": 132, "s6": 148 },
	"s3": {"server3": 52, "server4": 28, "s7": 4, "s8": 20},
	"s4": {"server7": 12, "server8": 20, "s7": 4, "s8": 28},
	"s5": {"s1": 140, "s2": 156, "s9": 132 ,"s10": 148 },
	"s6": {"s1": 136, "s2": 152, "s9": 128 ,"s10": 144 },
	"s7": {"s3": 12,"s4": 28, "s9": 4 ,"s10": 20},
	"s8": {"s3": 8,"s4": 24, "s9": 0 ,"s10": 16},
	"s9": {"s5": 132, "s6": 148, "s7": 140, "s8": 156},
	"s10":{"s5": 4, "s6": 28, "s7": 12, "s8": 20}
}

ipPrefix={"*":["192.168.111.1","0.0.0.0"],
		"server1":["192.168.111.1",	"255.255.255.128"],
		"server2":["192.168.111.128", "255.255.255.128"],
		"server5":["192.168.112.1",	"255.255.255.128"],
		"server6":["192.168.112.128", "255.255.255.128"],
		"server3":["192.168.113.1",	"255.255.255.128"],
		"server4":["192.168.113.128", "255.255.255.128"],
		"server7":["192.168.114.1",	"255.255.255.128"],
		"server8":["192.168.114.128", "255.255.255.128"]
		}

def find_switch_port(server_name):
	for switch_name, port_map in PORT_TRANS.items():
		if server_name in port_map:
			return switch_name, port_map[server_name]
	return None, None

def create_node(name, next_list, flow_list, timedelay_list, widthband_list):
	arc_dict = {}
	timedelay_dict = {}
	widthband_dict = {}
	for i in range(len(next_list)):
		arc_dict[next_list[i]] = flow_list[i]
		timedelay_dict[next_list[i]] = timedelay_list[i]
		widthband_dict[next_list[i]] = widthband_list[i]
	return Node(name, arc_dict, timedelay_dict, widthband_dict)


def updateRes(route,cost, node_list_cp,name_index_dict):
	for i in range(1,len(route) - 2):
		n1 = node_list_cp[name_index_dict[route[i]]]
		n2 = node_list_cp[name_index_dict[route[i + 1]]]
		# 正向更新 n1 -> n2 剩余流量减少
		if n2.name in n1.arc_dict.keys() and n1.arc_dict[n2.name] is not None:
			n1.arc_dict[n2.name] = n1.arc_dict[n2.name] - cost
		# 正向更新 n2 -> n1 剩余流量减少
		if n1.name in n2.arc_dict.keys() and n2.arc_dict[n1.name] is not None:
			n2.arc_dict[n1.name] = n2.arc_dict[n1.name] - cost
FLOW_ID=1
def increment_counter():
	global FLOW_ID
	FLOW_ID += 1

def get_flow_id():
	# crc16 = crcmod.predefined.Crc('crc-16')
    # """计算流的哈希值，并将哈希值映射到29位"""
    # flow_str = "{}/{},{}/{},{}".format(srcIp, srcprefix, dstIp, dstprefix, tcp_udp_dst_port)
    # # flow_id = crc16.update(flow_str.encode).crcValue
    # hash_obj = hashlib.sha256(flow_str.encode())
    # hash_int = int.from_bytes(hash_obj.digest(), byteorder='big')
    flow_id = FLOW_ID % (2 ** 13)
    increment_counter()
    # print(FLOW_ID)
    return flow_id

def format_server_name(name):
	if name.startswith('s'):
		return name
	else:
		return 'server' + name

def transFlowId(route,tcp_udp_dst_port):
	dst = format_server_name(route[-1])
	src = format_server_name(route[0])
	srcIp, srcprefix = ipPrefix[src]
	dstIp, dstprefix = ipPrefix[dst]
	flow_id = get_flow_id()
	return flow_id
	


def dinic_main(graph,inputFlowsList):
	# 创建有向图对象
	G = nx.DiGraph()
	# 添加节点
	for node in graph:
		G.add_node(node[0])
	# 添加有向边
	for node in graph:
		for i, next_node in enumerate(node[1]):
			G.add_edge(node[0], next_node, capacity=node[2][i])
	# 绘制网络图
	# pos = nx.spring_layout(G)
	# nx.draw(G, pos, with_labels=True, node_size=250, node_color='lightblue', font_size=10, font_weight='bold',
	#		 edge_color='gray', arrows=True)
	# edge_labels = nx.get_edge_attributes(G, 'capacity')
	# nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=5)
	# # 显示网络图
	# plt.title('Network Graph')
	# plt.show()

	data_stream_counts = [0]
	execution_times = [0]

	name_index_dict = dict()
	node_list = []

	cannot_route=[]
	route_list={}
	backroute_list = {}
	All_Paths = {}
	Path_With_Weight = {}

	Key = []
	threshold = 0.95
	max_width = 0

	count = 0

	for i in range(len(graph)):
		node_list.append(create_node(graph[i][0], graph[i][1], graph[i][2], graph[i][3], graph[i][4]))
		name_index_dict[graph[i][0]] = i
	start_time = datetime.now()
	
	sorted_inputFlowsList = sorted(inputFlowsList, key=lambda x: x[4], reverse=True)
	rate=40
	for inputFlow in sorted_inputFlowsList:
		flowId	= inputFlow[-1]
		tcp_udp_dst_port = inputFlow[2]
		# decimal_num = Decimal(inputFlow[4])
		# cost = math.ceil(decimal_num)
		# cost = 10*inputFlow[4]/20
		cost = rate*inputFlow[4]/20
		time_expect = inputFlow[5]
		observeflag = inputFlow[7]
		node_list_cp = copy.deepcopy(node_list)
		route = []
		back_route = []
		if inputFlow[0]!=inputFlow[1]:
			key = (inputFlow[0], inputFlow[1])
			# 起点与终点相同的数据流求一次所有路径
			if key not in Key:
				Key.append(key)
				all_paths = list(nx.all_simple_paths(G,inputFlow[0], inputFlow[1]))

				# to store the weight
				for path in all_paths:
					path.append( [0,0] )
					# to store the delay
					path.append(0)
					path.append(0)
				Path_With_Weight[key] = all_paths
				# Key.append((inputFlow[1], inputFlow[0]))

						
			# if key not in Path_With_Weight:
			# 	key = (inputFlow[1], inputFlow[0])
			# 求最大流路径
			# Path_With_Weight[key] : 所有可行路径
			satisPath=[]
			for path in Path_With_Weight[key]:
				LEN = len(path)
				if(LEN-4>6):
					pth=Path_With_Weight[key]
					pth.remove(path)
					Path_With_Weight[key]=pth
					continue
				
				weight = []
				delay = 0
				for i in range(1,LEN - 5):
					weight.append( node_list_cp[name_index_dict[path[i]]].arc_dict[path[i+1]] )
					delay = delay + node_list_cp[name_index_dict[path[i]]].timedelay[path[i+1]]
				# 160000ms
				# if len(weight)!=2:
				# 	path[-3] = [ min(weight) ,  len(weight[1:-1]) , np.mean(weight[1:-1])]
				# else:
				# 	path[-3] = [ min(weight) ,  len(weight) , np.mean(weight)]

				path[-2] = delay

				# 95000ms
				if len(weight)>=2:
					path[-3] = [ min(weight) ,  np.mean(weight[1:-1])]
				else:
					path[-3] = [ 0 ,  0]
				pathRoute=path[:-3]
				if path[-3][0]>=cost or len(pathRoute)<=3:
					satisPath.append(path)
					
				# path.append(min(node_list_cp[name_index_dict[path[i]]].arc_dict[path[i+1]] for i in range(LEN - 1))

			# 按容量由高至低排序
			# random.shuffle(Path_With_Weight[key])
			Path_With_Weight[key]=satisPath
			Path_With_Weight[key] = sorted(Path_With_Weight[key], key=lambda x: ( -x[-3][0], -x[-3][1] ) )
			
			j = 0
			for k , path in enumerate(Path_With_Weight[key]):
				LEN = len(path)
				width = []
				delay=path[-2]
				if float(delay) > float(time_expect):
					continue
				#if observe flow
				if observeflag == 0:
					if key == (inputFlow[0], inputFlow[1]):
						route = path[:-3]
					# else:
					# 	route = path[:-3][::-1]
					flow = path[-3][0]
					j = k
					break		
				else:
					for i in range(1,LEN - 5):
						width.append( node_list_cp[name_index_dict[path[i]]].widthband[path[i+1]] + cost / G[path[i]][path[i + 1]]['capacity'] )
					if(len(width)!=0):
						max_width = max(width)		
					else:
						max_width = 0
					if max_width <= threshold :
						if key == (inputFlow[0], inputFlow[1]):
							route = path[:-3]
						else:
							route = path[:-3][::-1]
						flow = path[-3][0]
						j = k
						break

					if max_width > threshold :
						if (len(back_route)==0):
							if key == (inputFlow[0], inputFlow[1]):
								back_route = path[:-3]
							else:
								back_route = path[:-3][::-1]
							back_flow = path[-3][0]
							Max = max_width
							j = k
	
								
			if len(route)==0 and len(back_route)==0 :
				cannot_route.append(inputFlow)
				print("Cannot find a route")
			else:
				if (len(route)!=0):
					if flow >= cost :
						path = Path_With_Weight[key][j]
						if observeflag == 1:
							path[-1] = max_width 
							LEN = len(path)
							for i in range(1,LEN - 5):
								node_list_cp[name_index_dict[path[i]]].widthband[path[i+1]] = node_list_cp[name_index_dict[path[i]]].widthband[path[i+1]] + cost / G[path[i]][path[i + 1]]['capacity']
								node_list_cp[name_index_dict[path[i+1]]].widthband[path[i]] = node_list_cp[name_index_dict[path[i]]].widthband[path[i+1]]

						# print(path)
						# print(flow)
						updateRes(route,cost,node_list_cp,name_index_dict)
						route_list[flowId] = {'route':route,'inputFlow':inputFlow}
					elif len(route)<=3 :
						path = Path_With_Weight[key][j]
						route_list[flowId] = {'route':route,'inputFlow':inputFlow}
					else :
						cannot_route.append(inputFlow)
						# print("Cannot find a route")
				else: 
					if (len(back_route)!=0):
						if back_flow >= cost and cost!=0:
							path = Path_With_Weight[key][j]
							if observeflag == 1:
								path[-1] = Max 
								LEN = len(path)
								for i in range(1,LEN - 5):
									node_list_cp[name_index_dict[path[i]]].widthband[path[i+1]] = node_list_cp[name_index_dict[path[i]]].widthband[path[i+1]] + cost / G[path[i]][path[i + 1]]['capacity']
									node_list_cp[name_index_dict[path[i+1]]].widthband[path[i]] = node_list_cp[name_index_dict[path[i]]].widthband[path[i+1]]

							# print(path)
							# print(back_flow)
							updateRes(back_route,cost,node_list_cp,name_index_dict)
							backroute_list[flowId] = {'back_route':back_route,'inputFlow':inputFlow}
							# route_list[flowId] = {'route':back_route,'inputFlow':inputFlow}


						else :
							cannot_route.append(inputFlow)
							# print("Cannot find a route")
				
				
			del(node_list)
			node_list = copy.deepcopy(node_list_cp)
		else:
			server,port=find_switch_port("server"+inputFlow[0])
			# backroute_list[flowId]={'route':[inputFlow[0], server, inputFlow[1]],'inputFlow':inputFlow}

		count = count + 1

		if count%1000 == 0:
			time_now = (datetime.now()-start_time).total_seconds()*1000
			data_stream_counts.append(count)
			execution_times.append(time_now)
	routeTable = dict(sorted(route_list.items(),key=lambda x : x[0]))
	# sorted(route_list, key=lambda x: x[4], reverse=True)
	# end_time = datetime.now()
	# elapsed_time = end_time - start_time
	# print("代码执行时间: {}毫秒".format(elapsed_time.total_seconds() * 1000))
	return routeTable,cannot_route,node_list,backroute_list



# route_list,cannot_route,node_list,backroute_list = dinic_main(graph,inputFlowsLists)


# # if len(cannot_route)!=0:
# print("*"*26+"the num of connot_route is %d" % len(cannot_route)+"*"*26)
# 	# print(cannot_route)
# print("*"*26+"the num of route_list is %d"% len(route_list)+"*"*26)
# print(route_list)
# print("*"*26+"the num of backroute_list is %d" % len(backroute_list)+"*"*26)
# # print(backroute_list)
# for i in node_list:
# 	print(i.name)
# 	print(i.arc_dict)
# 	print(i.widthband)