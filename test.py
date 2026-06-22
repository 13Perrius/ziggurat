import unittest
from dataclasses import dataclass
from typing import Any
import operator as op

from effect import *

@dataclass
class String(Effect[int]):
  s: str

def string_effc(e):
  def cont_fn(cont):
    return e.s + resume(cont, msg=7)
  return cont_fn

string_handler = Handler(retc = lambda x: x*"f", effc = string_effc)

class TestString(unittest.TestCase):
  def test(self):
    def fn():
      y = Perform(String("zz")) + 4
      w = y + Perform(String("gg"))
      z = y + Perform(String("yy"))
      a = w + z
      return a
    out = match_with_handler(fn(), string_handler)
    self.assertEqual(out, "zzggyy" + 36*"f")

  def test_internal(self):
    def fn():
      z = Perform(String("zz"))
      t = Perform(String(stre(z+5)))
      a = Perform(String(stre(z) + stre(t)))
      return a
    out = match_with_handler(fn(), string_handler)
    self.assertEqual(out, "zz1277fffffff")

@dataclass
class Read(Effect[Any]):
  key: Any

def read_effc(e):
  d = {"a": 10, 20: 30, "xs": {30:"success", 1:2}}
  def cont_fn(cont):
    return resume(cont, msg=looke(d, e.key))
  return cont_fn

read_handler = Handler(retc = lambda x: x, effc = read_effc)

def read(k): return Perform(Read(k))

class TestRead(unittest.TestCase):
  def test(self):
    def fn():
      a = read("a")
      b = read(a + 10)
      xs = read("xs") 
      return looke(xs, b)
    out = match_with_handler(fn(), read_handler)
    self.assertEqual(out, "success")

@dataclass
class Leaf:
  val: Any

@dataclass
class Node:
  l: "Tree"
  r: "Tree"

Tree = Node | Leaf 

def leaves(t):
  match t:
    case Leaf(v): return [v]
    case _: return leaves(t.l) + leaves(t.r)

def fold_map_tree(f, g, t):
  match t:
    case Leaf(v): return f(v)
    case Node(l, r): return g(fold_map_tree(f, g, l), fold_map_tree(f, g, r))

@dataclass
class Next(Effect[Any]):
  val: Any

@dataclass
class More:
  val: Any
  thunk: Callable

  def __iter__(self):
    val, thunk = self.val, self.thunk
    while True:
      yield val
      match thunk():
        case Done(): break
        case More(v, t):
          val = v
          thunk = t

class Done: pass

def next_effc(n):
  def cont_fn(cont):
    return More(n.val, lambda: resume(cont, n.val))
  return cont_fn

class TestNext(unittest.TestCase):
  def test_iter(self):
    next_handler = Handler(retc = lift(lambda _: Done()), effc = next_effc)
    t = Node(Node(Leaf(8), Leaf(9)), Leaf(4))
    acc = fold_map_tree(lambda x: Perform(Next(x)), op.add, t)
    out = match_with_handler(acc, next_handler)
    it = iter(leaves(t))
    for x in out:
      self.assertEqual(x, next(it))
