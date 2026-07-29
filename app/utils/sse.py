import json
import time


def sse_response(Response, stream_with_context, event_name, payload_func, version_getter, interval=0.2):
    """Simple SSE stream: initial payload immediately, then only on data changes.

    EventSource reconnects automatically in the browser if the connection drops.
    """
    def event_stream():
        last_version = None
        last_heartbeat = 0
        while True:
            try:
                version = version_getter()
                now = time.time()

                if last_version is None or version != last_version:
                    data = payload_func()
                    yield f"event: {event_name}\n"
                    yield "data: " + json.dumps(data, ensure_ascii=False, default=str) + "\n\n"
                    last_version = version
                    last_heartbeat = now
                elif now - last_heartbeat > 15:
                    yield ": keepalive\n\n"
                    last_heartbeat = now

                time.sleep(interval)
            except GeneratorExit:
                break
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                time.sleep(2)

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })


def status_sse_response(Response, stream_with_context, shell_status_payload_func, bridge_status_getter):
    def event_stream():
        last_status = None
        last_heartbeat = 0
        while True:
            try:
                now = time.time()
                current = str(bridge_status_getter())
                if current != last_status:
                    yield "event: status\n"
                    yield "data: " + json.dumps(shell_status_payload_func(), ensure_ascii=False) + "\n\n"
                    last_status = current
                    last_heartbeat = now
                elif now - last_heartbeat > 15:
                    yield ": keepalive\n\n"
                    last_heartbeat = now
                time.sleep(0.5)
            except GeneratorExit:
                break
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                time.sleep(2)

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })
