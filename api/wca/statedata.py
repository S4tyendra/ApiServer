from fastapi import APIRouter, HTTPException, Depends
from fastapi import Request

from api.wca.citiesinstate import sanitise
from api.wca.datab import world_db, TOKEN
from functions.apiwrapper import  refund_tokens, get_user

router = APIRouter()


@router.get("/getstatesincountry", )
async def get_states(
        country: str,
        request: Request,
):
    user = await get_user(request, accept=["tools-key"],tokens=-TOKEN)
    try:
        country = sanitise(country)
        db = await world_db()
        states = db.state.find({"country_name": {"$regex": country, "$options": "i"}})
        state_list = [state async for state in states if '_id' in state]
        if len(state_list) == 0:
            await refund_tokens(user['email'], TOKEN)
            raise HTTPException(status_code=404, detail="Country not found")
        state_list = [{**state, '_id': str(state['_id'])} for state in state_list]
        db.client.close()
        return state_list
    except HTTPException:
        raise
    except Exception as e:
        await refund_tokens(user['email'], TOKEN)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")