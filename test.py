import asyncio
import os.path
import time


async def function_one():
    print("Function one is done")
    await asyncio.sleep(5)
    os.path.join("./", "file.txt")
    await asyncio.sleep(5)
    print("Function one is done with file operation")


async def function_two():
    print("Function two is done")
    await asyncio.sleep(5)
    print("哈哈哈哈哈哈或")
    await asyncio.sleep(5)
    print("Function two is done with file operation")


async def main():
    await asyncio.gather(function_one(), function_two())


# 运行事件循环
asyncio.run(main())
