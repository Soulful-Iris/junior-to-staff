"""Local mechanism demonstration for 01-the-request-you-can-trace-end-to-end. No AWS resources are created."""
import asyncio,contextvars,json
request_id=contextvars.ContextVar('request_id')
async def handle(name,slow):
    token=request_id.set(name)
    try:
        for event in ('auth.ok','bookmark.saved','title.timeout' if slow else 'title.ok'):
            await asyncio.sleep(0)
            print(json.dumps({'request_id':request_id.get(),'event':event}))
    finally: request_id.reset(token)
async def main(): await asyncio.gather(handle('A',True),handle('B',False))
asyncio.run(main())
