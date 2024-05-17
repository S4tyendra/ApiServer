
from fastapi import APIRouter, Form, HTTPException, Request, Depends
from fastapi.responses import FileResponse

from functions.apiwrapper import api_key_auth, iiitk_auth, tokenconsuption

router = APIRouter()


def convert_to_pdf(mdc, title):
    from md2pdf.core import md2pdf
    
    md2pdf(
        pdf=f"temp/{title}.pdf",
        raw=mdc,
        css="font.css",
        
        extras=[
            "markdown.extensions.tables",
            "markdown.extensions.codehilite",
            "pymdownx.magiclink",
            "pymdownx.betterem",
            "pymdownx.superfences",
            "pymdownx.highlight",
            "pymdownx.snippets",
            "markdown.extensions.wikilinks",
            "markdown.extensions.toc",
            "pymdownx.arithmatex",
        ]
    )
    return f"temp/{title}.pdf"


@router.post("/sendpdf",dependencies=[Depends(iiitk_auth)]  )
async def send_pdf(request: Request, mdc=Form(...), title=Form(...)):
    try:
        file_name = convert_to_pdf(mdc, title)
        response = FileResponse(file_name, media_type="application/pdf", filename=file_name)
        return response
    except:
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            await tokenconsuption(api_key, 2)
        raise HTTPException(status_code=500, detail="Internal server error")