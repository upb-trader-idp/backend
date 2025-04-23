import time
from sqlalchemy.orm import Session
from database import TradingSessionLocal
from trades_model import Trade
from datetime import datetime, timezone

def match_trades():
    db: Session = TradingSessionLocal()
    try:
        # Get all buy orders sorted by highest price (most aggressive) and earliest time
        buy_orders = db.query(Trade).filter(
            Trade.flag == "unprocessed",
            Trade.action == "buy"
        ).order_by(Trade.price.desc(), Trade.created_at.asc()).all()

        for buy in buy_orders:
            # Re-fetch sell orders each time to reflect real-time quantities and ordering
            sell_orders = db.query(Trade).filter(
                Trade.flag == "unprocessed",
                Trade.action == "sell",
                Trade.symbol == buy.symbol,
                Trade.price <= buy.price
            ).order_by(Trade.created_at.asc()).all()

            for sell in sell_orders:
                if buy.quantity == 0:
                    break  # This buy order has been filled

                matched_qty = min(buy.quantity, sell.quantity)

                print(f"Matched {matched_qty} x {buy.symbol} at {sell.price} from {sell.username} to {buy.username}")

                # Update quantities
                buy.quantity -= matched_qty
                sell.quantity -= matched_qty

                if buy.quantity == 0:
                    buy.flag = "executed"

                if sell.quantity == 0:
                    sell.flag = "executed"

                db.commit()

    except Exception as e:
        print(f"Error in trade matching: {e}")
    finally:
        db.close()


def start_worker_loop():
    while True:
        match_trades()
        time.sleep(5)

if __name__ == "__main__":
    start_worker_loop()