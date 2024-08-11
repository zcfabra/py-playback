import json
from typing import Any, Dict, Literal, Protocol, Optional
from dataclasses import dataclass, asdict


@dataclass
class Walkable:
    name: str
    locals: Dict[str, Any]

    def _repr_(self) -> str:
        return f"{self.name}({self.locals})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'locals': {k: v for k, v in self.locals.items()}
        }


class IsWalkable(Protocol):
    __dict__: Dict[str, Any]


class PlaybackEncoder(json.JSONEncoder):
    def default(self, o):
        match o:
            case Walkable() as wlk: return wlk.to_dict()
            case Frame() as frm: return asdict(frm)
            case x: return super().default(x)


FrameEvent = Literal["call"] | Literal["return"] | Literal["line"]

@dataclass(slots=True)
class Frame:
    frame_type: FrameEvent
    line_no: int
    file_name: str
    fn_name: str
    locals: Optional[Dict[str, Any]] = None
    time_taken: Optional[float] = None

    def compact(self) -> str:
        out = ""

        match self.frame_type:
            case "call": out += '0'
            case "line": out += '1'
            case "return": out += '2'
        out += ','
        out += str(self.line_no)
        out += ','
        out += self.file_name
        out += ','
        out += self.fn_name
        out += ','
        out += json.dumps(self.locals, cls=PlaybackEncoder)
        out += ','
        out += str(self.time_taken) if self.time_taken else "null" 

        return out + "#"




    def __repr__(self) -> str:
        match self.frame_type:
            case 'call': frame_display = "CALL"
            case 'return': frame_display = "RTRN"
            case 'line': frame_display = "LINE"
        msg = f"| [{frame_display}] @ {self.line_no} ({self.fn_name})"
        if self.frame_type == 'line' \
        or (self.frame_type == 'call' and self.locals): 
            msg += f" <-- {self.locals}"
        msg += f" ({self.file_name.split('/')[-1]})"
        if self.time_taken:
            msg += f" ({self.time_taken:.8f}s)"
        return msg