from fastapi import APIRouter, HTTPException, Depends
from fastapi import Request

from api.countrystatesapi.datab import world_db
from functions.apiwrapper import api_key_auth
from functions.apiwrapper import tokenconsuption

router = APIRouter()


@router.get("/countrieslist", dependencies=[Depends(api_key_auth)])
async def get_countries(request: Request):
    try:
        db = await world_db()
        countries = db.countries.find()
        country_list = [country async for country in countries if '_id' in country]
        country_list = [{**country, '_id': str(country['_id'])} for country in country_list]
        return country_list
    except:
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            await tokenconsuption(api_key, 1)
        raise HTTPException(status_code=500, detail="Internal server error")
