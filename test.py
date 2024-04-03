


# import asyncio


# async def test():
#     for i in range(10):
#         print(f"Test {i}")
#         await asyncio.sleep(1)


# async def main():
#     for i in range(10):
#         print(f"Main {i}")
#         await asyncio.sleep(1)


# async def concurrent():
#     task1 = asyncio.create_task(test())
#     task2 = asyncio.create_task(main())
#     await task1
#     await task2


# asyncio.run(concurrent())


import json


with open(r'participle/千金/千金messages.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data)