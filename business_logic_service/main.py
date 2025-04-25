import time
from sqlalchemy.orm import Session
from shared.database import SessionLocal
from shared.models import User, Portfolio, Trade
from decimal import Decimal

SLEEP_TIME = 3 # seconds

def match_trades():
    main_db: Session = SessionLocal()

    try:

        # Get all buy orders sorted by highest price and earliest time
        buy_orders = main_db.query(Trade).filter(
            Trade.flag == "unprocessed",
            Trade.action == "buy"
        ).order_by(Trade.price.desc(), Trade.created_at.asc()).all()

        for buy in buy_orders:

            sell_orders = main_db.query(Trade).filter(
                Trade.flag == "unprocessed",
                Trade.action == "sell",
                Trade.symbol == buy.symbol,
                Trade.price <= buy.price
            ).order_by(Trade.created_at.asc()).all()
            

            for sell in sell_orders:
                if buy.quantity == 0:
                    break  # This buy order has been filled

                matched_qty = min(buy.quantity, sell.quantity)

                if matched_qty <= 0:
                    continue

                
                match_price = sell.price
                total = Decimal(str(matched_qty)) * Decimal(str(match_price))
                

                # Update seller's balance
                seller = main_db.query(User).filter(User.username == sell.username).first()
                
                if not seller:
                    raise Exception(f"[business_logic] Seller {sell.username} not found")
                
                seller.balance += total


                # Credit the buyer's balance with the difference between the sell price and his asking price
                buyer = main_db.query(User).filter(User.username == buy.username).first()

                if not buyer:
                    raise Exception(f"[business_logic] Buyer {buy.username} not found")
                
                original_total = Decimal(str(matched_qty)) * Decimal(str(buy.price))
                refund = original_total - total

                if refund > 0:
                    buyer.balance += refund


                # Update buyer's portfolio
                buyer_holding = main_db.query(Portfolio).filter_by(
                    username=buy.username,
                    symbol=buy.symbol
                ).first()

                if buyer_holding:
                    total_shares = buyer_holding.quantity + matched_qty

                    # Recalculate the average price
                    try:
                        new_price = (Decimal(str(buyer_holding.price)) * Decimal(str(buyer_holding.quantity)) + total) \
                            / Decimal(str(total_shares))

                        buyer_holding.price = new_price

                    except Exception as e:
                        print(f"[business_logic] Error calculating new price: {e}")
                        continue


                    buyer_holding.quantity = total_shares

                    try:
                        main_db.commit()
                    except Exception as e:
                        print(f"[business_logic] Commit failed: {e}")
                        main_db.rollback()
    
                else:

                    # Create a new portfolio entry for the buyer
                    buyer_holding = Portfolio(
                        username=buy.username,
                        symbol=buy.symbol,
                        quantity=matched_qty,
                        price=Decimal(str(match_price))
                    )
                    
                    # Add the new holding to the database
                    try:
                        main_db.add(buyer_holding)
                        main_db.commit()
                    except Exception as e:
                        print(f"[business_logic] Commit failed: {e}")
                        main_db.rollback()

                    main_db.refresh(buyer_holding)

                # Update trades
                buy.quantity -= matched_qty
                sell.quantity -= matched_qty

                if buy.quantity == 0:
                    buy.flag = "executed"

                if sell.quantity == 0:
                    sell.flag = "executed"

                # Commit changes
                main_db.commit()

    except Exception as e:
        print(f"[business_logic] Error in trade matching: {e}")
    finally:
        main_db.close()
    

if __name__ == "__main__":
    while True:
        match_trades()
        time.sleep(SLEEP_TIME)