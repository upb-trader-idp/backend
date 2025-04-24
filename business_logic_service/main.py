import time
from sqlalchemy.orm import Session
from database import TradingSessionLocal, UsersSessionLocal
from trades_model import Trade
from users_model import User, Portfolio
from decimal import Decimal

SLEEP_TIME = 3 # seconds

def match_trades():
    users_db: Session = UsersSessionLocal()
    trading_db: Session = TradingSessionLocal()

    try:

        # Get all buy orders sorted by highest price and earliest time
        buy_orders = trading_db.query(Trade).filter(
            Trade.flag == "unprocessed",
            Trade.action == "buy"
        ).order_by(Trade.price.desc(), Trade.created_at.asc()).all()

        for buy in buy_orders:

            sell_orders = trading_db.query(Trade).filter(
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
                

                print(f"Matched {matched_qty} shares of {buy.symbol} at {match_price} for {total}")

                # Update seller's balance
                seller = users_db.query(User).filter(User.username == sell.username).first()
                
                if not seller:
                    raise Exception(f"Seller {sell.username} not found")
                
                seller.balance += total

                # Update buyer's portfolio
                buyer_holding = users_db.query(Portfolio).filter_by(
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
                        print(f"Error calculating new price: {e}")
                        continue


                    buyer_holding.quantity = total_shares

                    print(f"New average price for {buyer_holding.symbol}: {new_price}")
                    try:
                        users_db.commit()
                    except Exception as e:
                        print(f"Commit failed: {e}")
                        users_db.rollback()
    
                else:
                    
                    print(f"Creating new portfolio for {buy.username}: {buy.symbol} - {matched_qty} shares at {match_price}")
                    buyer_holding = Portfolio(
                        username=buy.username,
                        symbol=buy.symbol,
                        quantity=matched_qty,
                        price=Decimal(str(match_price))
                    )
                    
                    users_db.add(buyer_holding)
                    try:
                        users_db.commit()
                    except Exception as e:
                        print(f"Commit failed: {e}")
                        users_db.rollback()

                    users_db.refresh(buyer_holding)

                # Update trades
                buy.quantity -= matched_qty
                sell.quantity -= matched_qty

                if buy.quantity == 0:
                    buy.flag = "executed"

                if sell.quantity == 0:
                    sell.flag = "executed"

                # Commit changes
                trading_db.commit()

    except Exception as e:
        print(f"Error in trade matching: {e}")
    finally:
        trading_db.close()
        users_db.close()
    

if __name__ == "__main__":
    while True:
        match_trades()
        time.sleep(SLEEP_TIME)