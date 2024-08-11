from dataclasses import fields
from enum import Enum, auto
from functools import partialmethod, wraps
import json
import os
import time
import sys
from types import FrameType
from typing import Any, Callable, Optional

from schemas import Frame, IsWalkable, Walkable, FrameEvent, PlaybackEncoder
from utils import get_tree


MAX_DEPTH = 10


class SerializeMode(Enum):
    AOS = auto()
    SOA = auto()
    COMPACT = auto()


class Playback:
    DIR = os.path.dirname(os.path.abspath(__file__))

    def __init__(
        self,
        walk_locals: bool = True,
        serialize_mode: SerializeMode = SerializeMode.AOS
    ):
        self.frames: list[Frame] = []

        self.__walk_locals = walk_locals
        self.__serialize_mode = serialize_mode
        self.__last_time: Optional[float] = None
        self.__active_untraced_scope = None

        self.__touched_files = set()

    def __enter__(self):
        sys.settrace(self.tracer)
        return self

    def __exit__(self, exc_type: str, exc_value: Exception, traceback: str):
        sys.settrace(None)

    def log_calls(self):
        for frame in self.frames:
            print(frame)

    def save_trace(self) -> None:
        with open("./playback.json", "w") as f:
            json.dump(self._serialize_trace(), f, cls=PlaybackEncoder)

    def _serialize_trace(
        self
    ) -> dict[str, list[Any]] | list[Frame] | str:
        frames = []
        match self.__serialize_mode:
            case SerializeMode.SOA: frames = self._to_soa()
            case SerializeMode.AOS: frames = self.frames
            case SerializeMode.COMPACT: frames = self._to_compact()

        return {
            'frames': frames,
            'files': self.__get_files()
        }

    def _to_soa(self) -> dict[str, list[Any]]:
        soa: dict[str, list[Any]] = {}
        for field in fields(Frame):
            field_values: list[Any] = []
            for frame in self.frames:
                field_values.append(getattr(frame, field.name))
            soa[field.name] = field_values
        return soa

    def _to_compact(self) -> str:
        out = ""
        for f in self.frames:
            out += f.compact()
        return out

    @classmethod
    def should_trace(cls, file_name: str) -> bool:
        return file_name.startswith(cls.DIR)

    def get_locals(self, f_locals: dict[str, Any]) -> dict[str, Any]:
        if self.__walk_locals:
            return {
                k: get_tree(v) if hasattr(v, "__dict__") else v
                for k, v in f_locals.items()
            }
        else:
            return dict(f_locals)

    def tracer(self, frame: FrameType, event: str, arg: Any):
        t = time.time()
        if self.__last_time is None:
            self.__last_time = t
            time_taken = None
        else:
            time_taken = t - self.__last_time
            self.__last_time = t

        fn_name = frame.f_code.co_name

        if fn_name == "__exit__":
            return
        self.__touched_files.add(file_name := frame.f_code.co_filename)

        line_no = frame.f_lineno

        match event:
            case "return":
                if self.__active_untraced_scope is None:
                    locals = self.get_locals(frame.f_locals)
                    self.push_return(file_name, line_no, fn_name, locals)
            case "line":
                if self.should_trace(file_name):
                    locals = self.get_locals(frame.f_locals)
                    self.push_line(file_name, line_no, fn_name, locals, time_taken)
            case "call":
                if (
                    (should_trace := self.should_trace(file_name))
                    or self.__active_untraced_scope is None
                ):
                    locals = None
                    if not should_trace:
                        locals = self.get_locals(frame.f_locals)
                    self.push_call(file_name, line_no, fn_name, locals)

                if not should_trace and self.__active_untraced_scope is None:
                    self.__active_untraced_scope = fn_name

            case "exception":
                pass
            case x:
                assert False, f"Should be unreachable: Found {x}"

        return self.tracer

    def push_frame(
        self,
        event_type: FrameEvent,
        file_name: str,
        line_no: int,
        fn_name: str,
        locals: Optional[dict[str, Any]],
        time_taken: Optional[float] = None
    ):
        f = Frame(
            frame_type=event_type,
            file_name=file_name,
            line_no=line_no,
            fn_name=fn_name,
            locals=locals,
            time_taken=time_taken
        )
        self.frames.append(f)

    push_call = partialmethod(push_frame, "call")
    push_line = partialmethod(push_frame, "line")
    push_return = partialmethod(push_frame, "return")

    @classmethod
    def wrap_playback(cls, func: Callable[[Any, ], Any]):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with cls() as pb:
                t = func(*args, **kwargs)
            pb.log_calls()
            pb.save_trace()
            return t
        return wrapper
    
    def __get_files(self) -> list[str]:
        files = {}
        for file in self.__touched_files:
            if self.should_trace(file):
                with open(file, 'r') as f:
                    files[file] = f.read()
        return files


