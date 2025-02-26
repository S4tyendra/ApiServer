from fastapi import APIRouter, HTTPException, Depends, Request

from api.wca.datab import world_db, TOKEN
from functions.apiwrapper import  refund_tokens, get_user

router = APIRouter()

@router.get("/getcitiesinstate")
async def get_cities(
        country: str,
        state: str,
        request: Request,
):
    user = await get_user(request, accept=["tools-key"],tokens=-TOKEN)
    try:
        country = sanitise(country)
        state = sanitise(state)
        db = await world_db()
        cities = db.cities.find(
            {
                "country_name": {"$regex": country, "$options": "i"},
                "state_name": {"$regex": state, "$options": "i"},
            }
        )
        cities_list = [city async for city in cities if "_id" in city]
        if len(cities_list) == 0:
            await refund_tokens(user['email'], 1)
            raise HTTPException(status_code=404, detail="Country or state not found")
        cities_list = [{**city, "_id": str(city["_id"])} for city in cities_list]
        db.client.close()
        return cities_list
    except HTTPException:
        raise
    except Exception as e:
        await refund_tokens(user['email'], 1)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def sanitise(state):
    if not state:
        return ""
    state = state.lower()
    state = (
        state.replace("'", "")
        .replace(".", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "")
    )
    return state
