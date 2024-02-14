from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, Depends
from functions.apiwrapper import api_key_auth
router = APIRouter()


@router.get("/countrieslist", dependencies=[Depends(api_key_auth)])
async def get_countries():
        return FileResponse('assets/countries.json', media_type='application/json')

