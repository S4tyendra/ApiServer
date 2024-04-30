
from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse

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


@router.post("/sendpdf",)
async def send_pdf(request: Request, mdc=Form(...), title=Form(...)):
    file_name = convert_to_pdf(mdc, title)
    response = FileResponse(file_name, media_type="application/pdf", filename=file_name)
    return response