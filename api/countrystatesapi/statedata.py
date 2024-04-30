from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, Depends
from api.countrystatesapi.citiesinstate import sanitise
from api.countrystatesapi.datab import world_db
from functions.apiwrapper import api_key_auth
router = APIRouter()


@router.get("/getstatesincountry", dependencies=[Depends(api_key_auth)])
async def get_states(country: str):
    contry = sanitise(country)
    db = await world_db()
    states = db.state.find({"country_name": {"$regex": contry, "$options": "i"}})
    state_list = [state async for state in states if '_id' in state]
    if len(state_list) == 0:
        raise HTTPException(status_code=404, detail="Country not found")
    state_list = [{**state, '_id': str(state['_id'])} for state in state_list]
    return state_list