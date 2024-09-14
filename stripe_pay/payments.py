import stripe
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router :APIRouter = APIRouter()

templates = Jinja2Templates(directory="templates")

STRIPE_PUBLIC_KEY = 'pk_live_51MsIyDSGMujHlWLW0Ja6bhr1e6TjCqdAb1gvTJRFeqBoUQr8kd2td1PDGXpDH2OLJy4Mrxe4bIzMjLZJcDoQCMs100L0UyWCm7'
STRIPE_SECRET_KEY = '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'

stripe.api_key = STRIPE_SECRET_KEY


@router.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/stripe_pay", response_class=JSONResponse)
def stripe_pay(request: Request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1OeameSGMujHlWLWSX9Hemlj',
            'quantity': 1,
        }],
        mode='payment',
        success_url=str(request.base_url) + '/thanks' + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=str(request.base_url),
    )
    return {
        'checkout_session_id': session['id'],
        'checkout_public_key': STRIPE_PUBLIC_KEY
    }


@router.get("/thanks", response_class=HTMLResponse)
async def thanks(request: Request):
    return templates.TemplateResponse("thanks.html", {"request": request})


@router.post("/stripe_webhook")
async def stripe_webhook(request: Request):
    print('WEBHOOK CALLED')

    # if request.headers.get("content-length") > '1048576':
    #     print('REQUEST TOO BIG')
    #     raise HTTPException(status_code=400, detail='REQUEST TOO BIG')

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = 'whsec_NuCENnOlUEWr59tqOzTJUZE8ZgrcjKzJ'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        print('INVALID PAYLOAD')
        raise HTTPException(status_code=400, detail='INVALID PAYLOAD')
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        print('INVALID SIGNATURE')
        raise HTTPException(status_code=400, detail='INVALID SIGNATURE')

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        print(session)
        line_items = stripe.checkout.Session.list_line_items(session['id'], limit=1)
        print(line_items['data'][0]['description'])

    return {}
