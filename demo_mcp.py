"""Standalone MCP service used in the offline product demo."""
import io
import os
import json
import sys

from mcp_client import VERSION


def pipe(stream, handle_id, mode):
    if stream is not None:
        return stream.buffer
    import ctypes
    import msvcrt
    get_handle = ctypes.windll.kernel32.GetStdHandle
    get_handle.restype = ctypes.c_void_p
    handle = get_handle(handle_id & 0xFFFFFFFF)
    flags = (os.O_RDONLY if mode == "rb" else os.O_WRONLY) | os.O_BINARY
    return os.fdopen(msvcrt.open_osfhandle(handle, flags), mode)


def serve():
    stdin = io.TextIOWrapper(pipe(sys.stdin, -10, "rb"), encoding="utf-8")
    stdout = io.TextIOWrapper(pipe(sys.stdout, -11, "wb"), encoding="utf-8", write_through=True)
    tool = {
        "name": "project_checklist",
        "description": "Return a short validation checklist for the supplied project.",
        "inputSchema": {"type": "object", "properties": {"project": {"type": "string"}},
                        "required": ["project"], "additionalProperties": False},
    }
    for line in stdin:
        request = json.loads(line)
        if "id" not in request:
            continue
        method = request.get("method")
        reply = {"jsonrpc": "2.0", "id": request["id"]}
        if method == "initialize":
            reply["result"] = {"protocolVersion": VERSION, "capabilities": {"tools": {}},
                               "serverInfo": {"name": "Course Checklist", "version": "1.0"}}
        elif method == "tools/list":
            reply["result"] = {"tools": [tool]}
        elif method == "tools/call" and request["params"].get("name") == tool["name"]:
            project = request["params"].get("arguments", {}).get("project", "")
            reply["result"] = {"content": [{"type": "text", "text":
                f"{project}：检查改动范围，运行测试，记录失败及恢复。"}]}
        elif method == "ping":
            reply["result"] = {}
        else:
            reply["error"] = {"code": -32601, "message": "Method not found"}
        stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        stdout.flush()


if __name__ == "__main__":
    serve()
