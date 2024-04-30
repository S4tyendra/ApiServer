from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, Depends
from functions.apiwrapper import api_key_auth

from api.countrystatesapi.datab import world_db
from fastapi import APIRouter, HTTPException, Depends
from functions.apiwrapper import api_key_auth
from api.countrystatesapi.datab import world_db
from bson import ObjectId
router = APIRouter()


router = APIRouter()

@router.get("/countrieslist", dependencies=[Depends(api_key_auth)])
async def get_countries():
        db = await world_db()
        countries = db.countries.find()
        country_list = [country async for country in countries if '_id' in country]
        country_list = [{**country, '_id': str(country['_id'])} for country in country_list]
        return country_list

