from __future__ import annotations
from typing import Callable, Generator, Generic, TypeVar
import operator as op
from dataclasses import dataclass

T = TypeVar('T')

class Effect(Generic[T]):
  pass

@dataclass
class Handler:
  retc: Callable
  effc: Callable

class GenDescr:
  def __get__(self, obj, owner):
    if obj is None: return self
    def _drive():
      if not obj.args:
        rcv = yield obj.val
      else:
        xs = []
        for a in obj.args:
          if a.mat:
            x = a.val
          else:
            x = yield from a.gen
          xs.append(x)
        rcv = obj.f(*xs)
      obj.mat = True
      obj.val = rcv
      return rcv
    return _drive()

def pure(x):
  if isinstance(x, Perform): return x
  return Perform(val=x, mat=True)

def lift(f):
  def _lifted(*args):
    if any(isinstance(a, Perform) for a in args):
      args = tuple(map(pure, args))
      return Perform(f=lift(f), args=args)
    else:
      return f(*args)
  return _lifted

stre = lift(str)

def look(m, k): 
    return m[k]

looke = lift(look)

class Perform:
  gen = GenDescr()
  def __init__(self, val=None, mat=False, f=lambda x: x, args=None):
    self.val = val
    self.mat = mat
    self.f = f
    self.args = args
  def __add__(self, other):
    return lift(op.add)(self, other)
  def __mul__(self, other):
    return lift(op.mul)(self, other)
  def __radd__(self, other):
    return lift(op.add)(other, self)
  def __rmul__(self, other):
    return lift(op.mul)(other, self)

@dataclass
class Cont:
  gen: Generator
  effc: Callable

def match_with_handler(comp, handler):
  comp = handler.retc(comp)
  return match_with(comp, handler.effc)

def match_with(comp, effc):
  if not isinstance(comp, Perform): return comp
  cont = Cont(comp.gen, effc)
  return resume(cont, None)

def resume(cont, msg):
  try:
    res = cont.gen.send(msg)
    return match_with(cont.effc(res)(cont), cont.effc)
  except StopIteration as e:
    return e.value

