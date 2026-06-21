import asyncio
from main import handle_generate

async def test():
    try:
        res = await handle_generate(
            hardware="SquareWoodBase",
            shape="cylinder",
            sides=4,
            height=120.0,
            diameter=120.0,
            thickness=3.0,
            files=None
        )
        print("SUCCESS:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test())
