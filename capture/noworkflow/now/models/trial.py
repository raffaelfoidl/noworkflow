# Copyright (c) 2014 Universidade Federal Fluminense (UFF), Polytechnic Institute of New York University.
# This file is part of noWorkflow. Please, consult the license terms in the LICENSE file.

from __future__ import absolute_import

import sys

from datetime import datetime
from collections import defaultdict, OrderedDict, Counter
from ..persistence import row_to_dict, persistence
from .. import utils
from .trial_activation_visitors import TrialGraphVisitor
from .trial_activation_visitors import TrialGraphCombineVisitor
from .activation import calculate_duration, FORMAT


class Trial(object):

    def __init__(self, trial_id, script=None, exit=False):
        if exit:
            last_trial_id = persistence.last_trial_id(script=script)
            trial_id = trial_id or last_trial_id
            if not 1 <= trial_id <= last_trial_id:
                utils.print_msg('inexistent trial id', True)
                sys.exit(1)

        self.trial_id = trial_id
        self._info = None

    @property
    def script(self):
        info = self.info()
        return info['script']

    @property
    def code_hash(self):
        info = self.info()
        return info['code_hash']
    
    def info(self):
        if self._info is None:
            self._info = row_to_dict(
                persistence.load_trial(self.trial_id).fetchone())
        return self._info

    def function_defs(self):
        return {
            function['name']: row_to_dict(function)
            for function in persistence.load('function_def', 
                                             trial_id=self.trial_id)
        }

    def head_trial(self, remove=False):
        parent_id = persistence.load_parent_id(self.script, remove=remove)
        return Trial(parent_id)

    def modules(self, map_fn=row_to_dict):
        dependencies = persistence.load_dependencies(self.trial_id)
        result = map(map_fn, dependencies)
        local = [dep for dep in result 
                 if dep['path'] and persistence.base_path in dep['path']]
        return local, result

    def environment(self):
        return {
            attr['name']: attr['value'] for attr in persistence.load(
                'environment_attr', trial_id=self.trial_id)
        }

    def file_accesses(self):
        file_accesses = persistence.load('file_access',
                                         trial_id=self.trial_id)
    
        result = []
        for file_access in file_accesses:
            stack = []
            function_activation = persistence.load('function_activation', id = file_access['function_activation_id']).fetchone()
            while function_activation:
                function_name = function_activation['name']
                function_activation = persistence.load('function_activation', id = function_activation['caller_id']).fetchone()
                if function_activation:
                    stack.insert(0, function_name)
            if not stack or stack[-1] != 'open':
                stack.append(' ... -> open')

            result.append({
                'name': file_access['name'],
                'mode': file_access['mode'],
                'buffering': file_access['buffering'],
                'content_hash_before': file_access['content_hash_before'],
                'content_hash_after': file_access['content_hash_after'],
                'timestamp': file_access['timestamp'],
                'stack': ' -> '.join(stack),
            })
        return result

    def activations(self):
        return persistence.load('function_activation', 
                                trial_id=self.trial_id,
                                order='start')

    def activation_graph(self):
        result_stack = []
        stack = [Single(act) for act in self.activations()]

        if not stack:
            return TreeElement()

        result_stack.append(stack.pop())
        while stack:
            next = result_stack.pop()
            previous = stack.pop()
            add_flow(stack, result_stack, previous, next)
        
        return result_stack.pop()

    def independent_activation_graph(self):
        graph = self.activation_graph()
        visitor = TrialGraphVisitor()
        graph.visit(visitor)
        return visitor.to_dict()

    def combined_activation_graph(self):
        graph = self.activation_graph()
        visitor = TrialGraphCombineVisitor()
        graph.visit(visitor)
        return visitor.to_dict()


class OrderedCounter(OrderedDict, Counter):
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__,
                            OrderedDict(self))
    def __reduce__(self):
        return self.__class__, (OrderedDict(self),)


class TreeElement(object):
    
    def __init__(self):
        self.duration = 0
        self.count = 1
        self.repr = ""

    def mean(self):
        if isinstance(self.duration, tuple):
            return (self.a.duration / self.a.count, 
                    self.b.duration / self.b.count)
        return self.duration / self.count

    def visit(self, visitor):
        return visitor.visit_default(self)

    def calculate_repr(self):
        pass

    def mix(self, other):
        pass

    def __hash__(self):
        return hash(self.__repr__())

    def __repr__(self):
        return self.repr


class Single(TreeElement):

    def __init__(self, activation):
        self.activation = activation
        self.activations = [activation]
        self.parent = activation['caller_id']
        self.count = 1
        self.id = activation['id']
        self.line = activation['line']
        self.name = activation['name']
        self.trial_id = activation['trial_id']
        self.duration = 0
        if activation['finish'] and activation['start']:
            self.duration = calculate_duration(activation)
        self.repr = "S({0}-{1})".format(self.line, self.name)

    def mix(self, other):
        self.count += other.count
        self.duration += other.duration
        self.activations += other.activations

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.line != other.line:
            return False
        if self.name != other.name:
            return False
        return True

    def name_id(self):
        return "{0} {1}".format(self.line, self.name)

    def visit(self, visitor):
        return visitor.visit_single(self)

    def to_dict(self, nid):
        return {
            'index': nid,
            'caller_id': self.parent,
            'name': self.name,
            'node': {
                'trial_id': self.trial_id,
                'line': self.line,
                'count': self.count,
                'duration': self.duration,
                'info': Info(self)
            }
        }

class Mixed(TreeElement):

    def __init__(self, activation):
        self.duration = activation.duration
        self.elements = [activation]
        self.parent = activation.parent
        self.id = activation.id
        self.repr = activation.repr
        self.count = 1

    def add_element(self, element):
        self.elements.append(element)
        self.count += element.count
        self.duration += element.duration

    def visit(self, visitor):
        return visitor.visit_mixed(self)

    def mix(self, other):
        self.elements += other.elements
        self.mix_results()

    def mix_results(self):
        initial = self.elements[0]
        for element in self.elements[1:]:
            initial.mix(element)


class Group(TreeElement):

    def __init__(self):
        self.nodes = OrderedDict()
        self.edges = OrderedDict()
        self.duration = 0
        self.parent = None
        self.count = 1
        self.repr = ""

    def initialize(self, previous, next):
        self.nodes[next] = Mixed(next)
        self.duration = next.duration
        self.next = next
        self.last = next
        self.add_subelement(previous)
        self.parent = next.parent
        return self

    def add_subelement(self, previous):
        next, self.next = self.next, previous
        if not previous in self.edges:
            self.edges[previous] = OrderedCounter()
        if not previous in self.nodes:
            self.nodes[previous] = Mixed(previous)
        else:
            self.nodes[previous].add_element(previous)
        self.edges[previous][next] += 1
        
    def calculate_repr(self):
        result = [
            "[{0}-{1}->{2}]".format(previous, count, next)
            for previous, edges in self.edges.items()
            for next, count in edges.items()
        ]
      
        self.repr = "G({0})".format(', '.join(result))

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if not self.edges == other.edges:
            return False
        return True

    def visit(self, visitor):
        return visitor.visit_group(self)

    def mix(self, other):
        for node, value in self.nodes.items():
            value.mix(other.nodes[node])


class Call(TreeElement):

    def __init__(self, caller, called):
        self.caller = caller
        self.called = called
        self.called.calculate_repr()
        self.parent = caller.parent
        self.count = 1
        self.id = self.caller.id
        self.duration = self.caller.duration
        self.repr = 'C({0}, {1})'.format(self.caller, self.called)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if not self.caller == other.caller:
            return False
        if not self.called == other.called:
            return False
        return True

    def visit(self, visitor):
        return visitor.visit_call(self)

    def mix(self, other):
        self.caller.mix(other.caller)
        self.called.mix(other.called)


class Dual(TreeElement):

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.parent = a.parent
        self.id = a.id
        self.duration = (a.duration, b.duration)
        self.count = (a.count, b.count)
        self.repr = "D({})".format(repr(a))

    def mix(self, other):
        self.a.mix(other.a)
        self.b.mix(other.b)
        self.duration = (a.duration, b.duration)
        self.count = (a.count, b.count)
        
    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.a != other.a:
            return False
        return True

    def calculate_repr(self):
        self.a.calculate_repr()
        self.b.calculate_repr()
        self.repr = "D({})".format(repr(self.a))

    def visit(self, visitor):
        return visitor.visit_dual(self)

    def name_id(self):
        return "{0} {1}".format(self.a.line, self.a.name)

    def to_dict(self, nid):
        return {
            'index': nid,
            'caller_id': self.parent,
            'name': self.a.name,
            'node1': {
                'line': self.a.line,
                'trial_id': self.a.trial_id,
                'count': self.a.count,
                'duration': self.a.duration,
                'info': Info(self.a),
            },
            'node2': {
                'line': self.b.line,
                'trial_id': self.b.trial_id,
                'count': self.b.count,
                'duration': self.b.duration,
                'info': Info(self.b)
            }
        }

class Branch(TreeElement):

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.duration = (a.duration, b.duration)
        self.count = (a.count, b.count)
        self.repr = "B({}, {})".format(repr(a), repr(b))

    def mix(self, other):
        self.a.mix(other.a)
        self.b.mix(other.b)
        self.duration = (a.duration, b.duration)
        self.count = (a.count, b.count)
        
    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.a != other.a:
            return False
        if self.b != other.b:
            return False
        return True

    def calculate_repr(self):
        self.a.calculate_repr()
        self.b.calculate_repr()
        self.repr = "B({}, {})".format(repr(self.a), repr(self.b))

    def visit(self, visitor):
        return visitor.visit_branch(self)


class DualMixed(TreeElement):

    def __init__(self, merge, a, b):
        self.merge = merge
        self.a = a
        self.b = b
        self.parent = a.parent
        self.id = a.id
        self.repr = a.repr
        self.duration = (a.duration, b.duration)
        self.count = (a.count, b.count)

    def visit(self, visitor):
        return visitor.visit_dualmixed(self)

    def mix(self, other):
        self.a.mix(other.a)
        self.b.mix(other.b)
        self.mix_results()

    def mix_results(self):
        self.a.mix_results()
        self.b.mix_results()
        self.duration = (self.a.duration, self.b.duration)
        self.count = (self.a.count, self.b.count)


class Info(object):

    def __init__(self, single):
        self.title = "Trial {trial}<br>Function <b>{name}</b> called at line {line}".format(
            trial=single.trial_id, name=single.name, line=single.line)
        self.activations = []
        self.duration = ""
        self.mean = ""
        self.extract_activations(single)

    def update_by_node(self, node):
        self.duration = self.duration_text(node['duration'], node['count'])
        self.mean = self.mean_text(node['mean'])
        self.activations.sort(key=lambda a: a[0])

    def add_activation(self, activation):
        self.activations.append(
            (datetime.strptime(activation['start'], FORMAT), activation))

    def extract_activations(self, single):
        for activation in single.activations:
            self.add_activation(activation)

    def duration_text(self, duration, count):
        return "Total duration: {} microseconds for {} activations".format(
            duration, count)

    def mean_text(self, mean):
        return "Mean: {} microseconds per activation".format(mean)

    def activation_text(self, activation):
        values = persistence.load('object_value', 
                                  function_activation_id=activation['id'],
                                  order='id')
        values = [value for value in values if value['type'] == 'ARGUMENT']
        result = [
            "",
            "Activation #{id} from {start} to {finish} ({dur} microseconds)"
                .format(dur=calculate_duration(activation), **activation),
        ]
        if values:
            result.append("Arguments: {}".format(
                ", ".join("{}={}".format(value["name"], value["value"])
                    for value in values)))
        return result + [
            "Returned {}".format(activation['return'])
        ]

    def __repr__(self):
        result = [self.title, self.duration, self.mean]
        for activation in self.activations:
            result += self.activation_text(activation[1])

        return '<br/>'.join(result)



def join(a, b):
    if a == b:
        return Dual(a, b)
    return Branch(a, b)

def sequence(previous, next):
    if isinstance(next, Group):
        next.add_subelement(previous)
        return next
    return Group().initialize(previous, next)


def add_flow(stack, result_stack, previous, next):
    if previous.parent == next.parent:
        # Same function level
        result_stack.append(sequence(previous, next))

    elif previous.id == next.parent:
        # Previously called next
        # if top of result_stack is in the same level of call: 
        #   create sequece or combine results
        # if top of result_stack is in a higher level, put Call on top of pile
        if result_stack:
            add_flow(stack, result_stack, Call(previous, next), result_stack.pop())
        else: 
            result_stack.append(Call(previous, next))
    else:
        # Next is in a higher level
        # Put previous on top of result_stack
        result_stack.append(next)
        result_stack.append(previous)