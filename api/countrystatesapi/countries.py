from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/countrieslist")
async def get_countries():
        return FileResponse('assets/countries.json', media_type='application/json')

