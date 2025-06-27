from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from db_helper import (
    get_next_order_id,
    insert_order_item,
    insert_order_tracking,
    get_total_order_price,
    get_order_status
)
from generic_helper import extract_session_id
import traceback

app = FastAPI()


def normalize_intent(intent_name: str) -> str:
    return intent_name.split(":")[0] if ":" in intent_name else intent_name

@app.post("/")
async def handle_dialogflow_webhook(request: Request):
    try:
        body = await request.json()
        raw_intent = body["queryResult"]["intent"]["displayName"]
        intent_name = normalize_intent(raw_intent)
        session = body.get("session", "")
        session_id = extract_session_id(session)

        print("Raw intent:", raw_intent)
        print("Normalized intent:", intent_name)

        contexts = body["queryResult"].get("outputContexts", [])
        order_context = next((ctx for ctx in contexts if "ongoing-order" in ctx["name"]), None)
        tracking_context = next((ctx for ctx in contexts if "ongoing-tracking" in ctx["name"]), None)

        parameters = order_context.get("parameters", {}) if order_context else {}
        food_items = parameters.get("food-item", [])
        quantities = parameters.get("number", [])
        order_id = parameters.get("order_id")
        previous_items = parameters.get("all_items", [])

        if isinstance(food_items, str):
            food_items = [food_items]
        if isinstance(quantities, (int, float)):
            quantities = [quantities]
        if isinstance(previous_items, str):
            previous_items = [previous_items]

        # 🟡 ADD ITEMS TO ORDER
        if intent_name == "order.add-context":
            if not order_id:
                order_id = get_next_order_id()
                insert_order_tracking(order_id, "in progress")
                previous_items = []

            added_items = []
            for item, qty in zip(food_items, quantities):
                cleaned_item = str(item).strip().title()
                rcode = insert_order_item(cleaned_item, int(float(qty)), order_id)
                if rcode != -1:
                    entry = f"{int(qty)} x {cleaned_item}"
                    added_items.append(entry)
                    previous_items.append(entry)
                else:
                    return JSONResponse(content={
                        "fulfillmentText": f"❌ Failed to add '{item}'. Please try again."
                    })

            order_summary = " and ".join(previous_items)
            return JSONResponse(content={
                "fulfillmentText": f"✅ {order_summary} added to your order. Anything else?",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/ongoing-order",
                        "lifespanCount": 5,
                        "parameters": {
                            "food-item": food_items,
                            "number": quantities,
                            "order_id": order_id,
                            "session_id": session_id,
                            "all_items": previous_items
                        }
                    }
                ]
            })

        # ✅ COMPLETE ORDER
        elif intent_name in ["complete-order", "order.complete-context", "done", "no", "finish-order"]:
            if not order_id:
                return JSONResponse(content={
                    "fulfillmentText": "❌ No active order found. Please start a new one."
                })

            total_price = get_total_order_price(order_id)
            return JSONResponse(content={
                "fulfillmentText": (
                    f"✅ Order placed successfully!\n"
                    f"🆔 Order ID: {order_id}\n"
                    f"💰 Total: ₹{total_price:.2f}\n\n"
                    "You can track your order using your order ID."
                ),
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/ongoing-tracking",
                        "lifespanCount": 5,
                        "parameters": {
                            "order_id": order_id,
                            "session_id": session_id
                        }
                    }
                ]
            })

        # 📦 TRACK ORDER — now robust for ID in reply
        elif intent_name in ["track.order", "track.order-id"]:
            order_id = None

            # STEP 1: From intent parameters
            intent_params = body["queryResult"].get("parameters", {})
            if "order_id" in intent_params:
                order_id = intent_params["order_id"]

            # STEP 2: From tracking context
            if not order_id and tracking_context:
                order_id = tracking_context.get("parameters", {}).get("order_id")

            # STEP 3: From output contexts
            if not order_id:
                for ctx in body["queryResult"].get("outputContexts", []):
                    if "parameters" in ctx and "order_id" in ctx["parameters"]:
                        order_id = ctx["parameters"]["order_id"]
                        break

            print("FINAL TRACK ORDER ID:", order_id)

            if not order_id:
                return JSONResponse(content={
                    "fulfillmentText": "📦 Please provide your order ID to track it."
                })

            try:
                order_id = int(order_id)
            except ValueError:
                return JSONResponse(content={
                    "fulfillmentText": "❌ Invalid order ID format. Please enter a valid number."
                })

            status = get_order_status(order_id)

            if status:
                return JSONResponse(content={
                    "fulfillmentText": f"📦 Your order {order_id} is currently **{status}**."
                })
            else:
                return JSONResponse(content={
                    "fulfillmentText": f"❌ No order found with ID {order_id}. Please check and try again."
                })

        # ❌ FALLBACK
        else:
            return JSONResponse(content={
                "fulfillmentText": "🤖 Sorry, I didn't understand that request."
            })

    except Exception:
        print(traceback.format_exc())
        return JSONResponse(content={
            "fulfillmentText": "🚨 Technical error occurred. Please try again."
        })
