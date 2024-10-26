import stripe
from fastapi import APIRouter, Request, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional
from fastapi.templating import Jinja2Templates

router = APIRouter()

STRIPE_PUBLIC_KEY = '***'
STRIPE_SECRET_KEY = '***'

stripe.api_key = STRIPE_SECRET_KEY
stripe.api_version = "2020-08-27"  # Use the latest API version recommended for India

templates = Jinja2Templates(directory="templates")


async def get_stripe_session(request: Request):
    return stripe.checkout.Session.create(
        payment_method_types=[
    "card"
]
,
        customer_email="2022kucp1022@iiitkota.ac.in",
        line_items=[{
            'price': "price_1QE5LwSGMujHlWLWUmMBkxaD",
            'quantity': 1,
        }],
        mode='payment',
        success_url=str(request.base_url) + 'thanks?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=str(request.base_url),
    )


@router.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "stripe_public_key": STRIPE_PUBLIC_KEY})


@router.get("/stripe_pay", response_class=JSONResponse)
async def stripe_pay(request: Request, session: dict = Depends(get_stripe_session)):
    return {
        'checkout_session_id': session.id,
        'checkout_public_key': STRIPE_PUBLIC_KEY
    }


@router.get("/thanks", response_class=HTMLResponse)
async def thanks(request: Request, session_id: Optional[str] = None):
    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            return templates.TemplateResponse("thanks.html", {"request": request, "paid": True})
    return templates.TemplateResponse("thanks.html", {"request": request, "paid": False})


@router.post("/stripe_webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_SECRET_KEY
        )
        print("Webhook data:", event)
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Fulfill the purchase...
            print("Payment was successful.")
        # Add more event handling as needed
    except ValueError as e:
        # Invalid payload
        return JSONResponse(status_code=400, content={"error": str(e)})
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JSONResponse(status_code=400, content={"error": str(e)})

    return JSONResponse(status_code=200, content={"status": "success"})