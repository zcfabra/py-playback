import subprocess
from typing import Any

from main import Playback


class Adder():
    def __init__(self) -> None:
        self.added = 0
        self.ref = self

    def add(self, a: int, b: int) -> None:
        self.added += (a + b)

    def get_added(self):
        adder = Adder()
        adder.add(self.added, self.added)
        return self.added


def test_func():
    x = 10 + 10
    y = 20 + x
    (adder := Adder()).add(x, y)
    return adder.get_added()

class A:
    def __init__(self):
        self.c = None

    def set_c(self, c):
        self.c = c

    def do_nothing(self):
        _ = self.c


class B:
    def __init__(self, a):
        self.a = a


class C:
    def __init__(self, b):
        self.b = b

def test_cycle():
    a = A()
    b = B(a)
    c = C(b)
    a.set_c(c)

    a.do_nothing()


def ident(i: Any) -> Any:
    return i


@Playback.wrap_playback
def main():
    test_func()
    i = ident("hi")
    print(f"Printing: {i}")
    x = pow(10, 20)
    test_cycle()

    subprocess.run("ls -a".split(), capture_output=True, check=True)


main()