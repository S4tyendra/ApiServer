from fastapi import APIRouter, HTTPException, Depends
from fastapi import Request
from icecream import ic
from api.countrystatesapi.datab import world_db
from functions.apiwrapper import api_key_auth, get_user
from functions.apiwrapper import refund_tokens

TOKEN = 1
router = APIRouter()


@router.get("/countrieslist", dependencies=[Depends(lambda: api_key_auth(tokens=-TOKEN, accept=["tools-key"]))])
async def get_countries(
        request: Request,
):
    current_user = await get_user(request, accept=["tools-key"])
    ic(current_user)
    try:
        db = await world_db()
        countries = db.countries.find()
        country_list = [country async for country in countries if '_id' in country]
        country_list = [{**country, '_id': str(country['_id'])} for country in country_list]
        db.client.close()
        return country_list
    except Exception as e:
        await refund_tokens(current_user['email'], TOKEN)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
