from typing import Any
from main import MAX_DEPTH
from schemas import IsWalkable, Walkable


def get_tree(
    root: IsWalkable,
    depth: int = 0,
    cache: dict[int, Walkable] | None = None
) -> Walkable:
    if cache is None:
        cache = {}

    cache[id(root)] = True

    if depth > MAX_DEPTH:
        return Walkable(name="MAX_DEPTH", locals={})

    out: dict[str, Any] = {}
    for k, v in root.__dict__.items():
        # if id(v) in cache:
        #     out[k] = f'<{get_cls_name_opt(v, k)}>'
        if root is v:
            # Avoid infinite recursion by replacing self-references
            # with a special '<self>’ marker
            out[k] = '<self>'
        elif id(v) in cache:
            out[k] = f'{get_cls_name_opt(v, "Walked")}'
        elif hasattr(v, '__dict__'):
            cache[id(v)] = True
            out[k] = get_tree(v, depth + 1, cache)
        else:
            out[k] = v

            
    class_name = get_cls_name_opt(root, "Walked")
    return Walkable(name=class_name, locals=out)

def get_cls_name_opt(x: Any, fallback: str):
    if hasattr(x, '__class__'):
        return x.__class__.__name__
    else:
        return fallback
