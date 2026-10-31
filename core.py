from __future__ import annotations
from typing import Callable, Generator, Generic, TypeVar, Any
import operator as op
from dataclasses import dataclass

T = TypeVar('T')

class Effect(Generic[T]): pass

@dataclass
class Handler:
  retc: Callable
  effc: Callable

class GenDescr:
  def __get__(self, obj, owner):
    if obj is None: return self
    def drive():
      if not obj.args:
        rcv = yield obj.val
      else:
        xs = []
        for a in obj.args: xs.append(a.val if a.mat else (yield from a.gen))
        rcv = obj.f(*xs)
      obj.mat, obj.val = True, rcv
      return rcv
    return drive()

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

def look(m, k): return m[k]

looke = lift(look)

@dataclass
class Perform:
  gen = GenDescr()
  val: Any|None = None
  mat: bool = False
  f: Callable|None = None
  args: tuple[Any, ...]|None = None
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

