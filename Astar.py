import math
from logging_manager import log_debug
import math
from logging_manager import log_debug
class Problem:
    def __init__(self, start_node, goal_node, graph, busy_points):
        self.start = start_node
        self.goal = goal_node
        self.graph = graph
        self.busy_points = busy_points
    def get_edge_cost(self, state1, state2):
        return math.sqrt((state1[0]-state2[0])**2 + (state1[1]-state2[1])**2) * 111320
    def get_heuristic(self, state):
        h = self.get_edge_cost(state, self.goal)
        state_rounded = (round(state[0], 4), round(state[1], 4))
        if state_rounded in self.busy_points:
            h += 5000
            log_debug(f"Penalizăm nodul: {state}")
        return h
    def get_root(self):
        return self.start
    def get_successors(self, state):
        state_tuple = tuple([round(state[0], 4), round(state[1], 4)])
        return self.graph.get(state_tuple, [])
    def is_goal(self, state):
        return math.dist(state, self.goal) < 0.001

class Node:
    depth=0
    f = 0
    g = 0
    h = 0
    def __init__(self, state, operator, parent):
        self.state = state
        self.parent = parent
        self.operator = operator

def is_in_closed_with_smaller_g(successor_node:Node, closed_list):
    if successor_node.state in closed_list.keys():
        if closed_list[successor_node.state].g <= successor_node.g:
            return True
    return False

def is_in_open_with_smaller_g(successor_node:Node, open_list):
    for node in open_list:
        if node.state == successor_node.state and node.g <= successor_node.g:
            return True
    return False

def is_case_for_parent_pruning(successor_node:Node, current_node):
    return current_node.parent is not None and successor_node.state == current_node.parent.state

def shorter_road(successor_node:Node, open_list, closed_list):
    return not is_in_open_with_smaller_g(successor_node, open_list) and not is_in_closed_with_smaller_g(successor_node, closed_list)

class AstarAlgorithm:
    def solve(self, problem:Problem):
        open_list=[]
        closed_list={}
        root=Node(problem.get_root(), "", None)
        root.g = 0
        root.h = problem.get_heuristic(root.state)
        root.f = root.g + root.h
        open_list.append(root)
        while len(open_list) >= 1:
            current_node = min(open_list, key=lambda n: n.f)
            open_list.remove(current_node)
            log_debug(f"Explorăm nodul: {current_node.state} | Vecini găsiți: {len(problem.get_successors(current_node.state))}")
            if problem.is_goal(current_node.state):
                return self.build_solution(current_node), current_node.g
            else:
                for fiu in problem.get_successors(current_node.state):
                    successor_node = Node(fiu, "", current_node)
                    successor_node.depth = current_node.depth + 1
                    successor_node.g = current_node.g + problem.get_edge_cost(current_node.state, fiu)
                    successor_node.h = problem.get_heuristic(successor_node.state)
                    successor_node.f = max(current_node.f, successor_node.g + successor_node.h)
                    #successor_node.f =successor_node.g + successor_node.h
                    if not is_case_for_parent_pruning(successor_node, current_node):
                        if shorter_road(successor_node, open_list, closed_list):
                            open_list.append(successor_node)
                closed_list[current_node.state] = current_node
        return None, float('inf')

    def build_solution(self, node):
        path = []
        curr = node
        while curr is not None:
            path.append(list(curr.state))
            curr = curr.parent
        return path[::-1]