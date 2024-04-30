import os.path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from api.countrystatesapi.datab import world_db
from functions.apiwrapper import api_key_auth

router = APIRouter()


@router.get("/getcitiesinstate", dependencies=[Depends(api_key_auth)])
async def get_cities(country: str, state: str):
    contry = sanitise(country)
    state = sanitise(state)
    db = await world_db()
    cities = db.cities.find({"country_name": {"$regex": contry, "$options": "i"}, "state_name": {"$regex": state, "$options": "i"}})
    cities_list = [city async for city in cities if '_id' in city]
    if len(cities_list) == 0:
        raise HTTPException(status_code=404, detail="Country or state not found")
    cities_list = [{**state, '_id': str(state['_id'])} for state in cities_list]
    return cities_list


def sanitise(state):
    if not state:
        return ""
    state = state.lower()
    state = state.replace("'", "").replace(".", "").replace("-", "").replace("(", "").replace(")", "").replace("/", "")
    return state
