from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, Depends
from functions.apiwrapper import api_key_auth

from api.countrystatesapi.datab import connect_to_database
router = APIRouter()


@router.get("/countrieslist", dependencies=[Depends(api_key_auth)])
async def get_countries():
        db = await connect_to_database()
        countries = await db.countries.find()
        print(countries)
        return FileResponse('assets/countries.json', media_type='application/json')

