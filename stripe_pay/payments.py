import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
router :APIRouter = APIRouter()

templates = Jinja2Templates(directory="templates")

STRIPE_PUBLIC_KEY = 'pk_live_51MsIyDSGMujHlWLW0Ja6bhr1e6TjCqdAb1gvTJRFeqBoUQr8kd2td1PDGXpDH2OLJy4Mrxe4bIzMjLZJcDoQCMs100L0UyWCm7'
STRIPE_SECRET_KEY = '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'





stripe.api_key = STRIPE_SECRET_KEY

async def get_stripe_session(request: Request):
    return stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': "price_1OeameSGMujHlWLWSX9Hemlj",
            'quantity': 1,
        }],
        mode='payment',
        success_url=str(request.base_url) + 'thanks?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=str(request.base_url),
    )

@router.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/stripe_pay", response_class=JSONResponse)
async def stripe_pay(request: Request, session: dict = Depends(get_stripe_session)):
    return {
        'checkout_session_id': session['id'],
        'checkout_public_key': settings.STRIPE_PUBLIC_KEY
    }

@router.get("/thanks", response_class=HTMLResponse)
async def thanks(request: Request, session_id: Optional[str] = None):
    return templates.TemplateResponse("thanks.html", {"request": request, "session_id": session_id})

@router.post("/stripe_webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid payload')
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail='Invalid signature')

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_completed_checkout(session)

    return JSONResponse(status_code=200)

async def handle_completed_checkout(session: dict):
    # Implement your logic for handling completed checkouts here
    # For example, you might want to:
    # 1. Retrieve the customer information
    # 2. Update your database
    # 3. Send a confirmation email
    # 4. etc.

    line_items = stripe.checkout.Session.list_line_items(session['id'], limit=1)
    print(f"Completed checkout for: {line_items['data'][0]['description']}")