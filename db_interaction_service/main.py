from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timezone
from jose import jwt
import os

from shared.database import SessionLocal
from shared.models import User, Portfolio, Trade
from shared.schemas import BalanceUpdate, PortfolioItem, TradeItem, TradeUpdate
from typing import List

app = FastAPI()

# JWT config
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM")

def get_main_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_sub_from_jwt(authorization: str = Header(...)) -> str:
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    

# Balance endpoints
@app.get("/get_balance")
def get_balance(username: str = Depends(get_sub_from_jwt),
                db: Session = Depends(get_main_db)):
    
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"username": username, "balance": float(user.balance)}


@app.post("/add_balance")
def add_balance(update: BalanceUpdate,
                username: str = Depends(get_sub_from_jwt),
                db: Session = Depends(get_main_db)):
    
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update.amount < 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    user.balance += Decimal(str(update.amount))
    user.added_balance += Decimal(str(update.amount))

    try:
        db.commit()
    except Exception as e:
        print(f"[db_interaction/add_balance] Commit failed: {e}")
        db.rollback()

    db.refresh(user)

    return {"msg": f"Balance updated", "new_balance": float(user.balance)}


@app.post("/remove_balance")
def remove_balance(update: BalanceUpdate,
                   username: str = Depends(get_sub_from_jwt),
                   db: Session = Depends(get_main_db)):
    
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    amount = Decimal(str(update.amount))

    if user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    user.balance -= amount

    try:
        db.commit()

    except Exception as e:
        print(f"[db_interaction/remove_balance] Commit failed: {e}")
        db.rollback()

    db.refresh(user)

    return {"msg": f"Balance removed", "new_balance": float(user.balance)}


# Trade endpoint
@app.post("/add_trade")
def add_trade(trade: TradeItem,
              username: str = Depends(get_sub_from_jwt),
              main_db: Session = Depends(get_main_db)):
    
    user = main_db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_cost = Decimal(str(trade.quantity * trade.price))

    if trade.action == "buy":
        if user.balance < total_cost:
            raise HTTPException(status_code=400, detail="Insufficient balance for buy order")

        user.balance -= total_cost 
        
        try:
            main_db.commit()
        except Exception as e:
            print(f"[db_interaction/add_trade] Commit failed: {e}")
            main_db.rollback()

        main_db.refresh(user)

    elif trade.action == "sell":
        holding = main_db.query(Portfolio).filter(
            Portfolio.username == username,
            Portfolio.symbol == trade.symbol
        ).first()

        if not holding or holding.quantity < trade.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient shares of {trade.symbol} to sell")

        # Remove shares from portfolio
        holding.quantity -= trade.quantity

        if holding.quantity == 0:
            try:
                main_db.delete(holding)

            except Exception as e:
                print(f"[db_interaction/add_trade] Error deleting holding: {e}")
                main_db.rollback()

        try:
            main_db.commit()

        except Exception as e:
            print(f"[db_interaction/add_trade] Commit failed: {e}")
            main_db.rollback()

        main_db.refresh(user)

    else:
        raise HTTPException(status_code=400, detail="Invalid trade action")
    

    new_trade = Trade(username=username, **trade.model_dump(exclude={"created_at"}))

    try:
        main_db.add(new_trade)
        main_db.commit()
    except Exception as e:
        print(f"[db_interaction/add_trade] Commit failed: {e}")
        main_db.rollback()
        
    main_db.refresh(new_trade)

    return {"msg": "Trade added", "trade_id": new_trade.id}


@app.put("/edit_trade/{trade_id}")
def edit_trade(trade_id: int,
               update: TradeUpdate,
               username: str = Depends(get_sub_from_jwt),
               db: Session = Depends(get_main_db)):
    
    # Get the trade
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.username == username
    ).first()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Check if trade is already processed
    if trade.flag != "unprocessed":
        raise HTTPException(status_code=400, detail="Cannot edit processed trades")
    
    try:
        if trade.action == "buy":
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Calculate the difference in cost
            old_cost = Decimal(str(trade.quantity * trade.price))
            new_cost = Decimal(str(update.quantity * update.price)) if update.quantity is not None and update.price is not None else \
                      Decimal(str(update.quantity * trade.price)) if update.quantity is not None else \
                      Decimal(str(trade.quantity * update.price)) if update.price is not None else old_cost
            
            # If increasing cost, check if user has enough balance
            if new_cost > old_cost:
                if user.balance < (new_cost - old_cost):
                    raise HTTPException(status_code=400, detail="Insufficient balance for trade modification")
                user.balance -= (new_cost - old_cost)
            # If decreasing cost, refund the difference
            else:
                user.balance += (old_cost - new_cost)
            
            # Update trade details
            if update.quantity is not None:
                trade.quantity = update.quantity
            if update.price is not None:
                trade.price = Decimal(str(update.price))
            
            # Update the timestamp
            trade.created_at = datetime.now(timezone.utc)
            
            db.commit()
            
        elif trade.action == "sell":
            holding = db.query(Portfolio).filter(
                Portfolio.username == username,
                Portfolio.symbol == trade.symbol
            ).first()
            
            if not holding:
                raise HTTPException(status_code=404, detail=f"No holding found for {trade.symbol}")
            
            # Calculate the difference in quantity
            old_quantity = trade.quantity
            new_quantity = update.quantity if update.quantity is not None else old_quantity
            
            # If increasing quantity, check if user has enough shares
            if new_quantity > old_quantity:
                if holding.quantity < (new_quantity - old_quantity):
                    raise HTTPException(status_code=400, detail=f"Insufficient shares of {trade.symbol} to modify trade")
                holding.quantity -= (new_quantity - old_quantity)
            # If decreasing quantity, return the difference to portfolio
            else:
                holding.quantity += (old_quantity - new_quantity)
            
            # Update trade details
            if update.quantity is not None:
                trade.quantity = update.quantity
            if update.price is not None:
                trade.price = Decimal(str(update.price))
            
            # Update the timestamp
            trade.created_at = datetime.now(timezone.utc)
            
            db.commit()
            
    except Exception as e:
        print(f"[db_interaction/edit_trade] Error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update trade")
    
    return {"msg": "Trade updated successfully", "trade_id": trade.id}


@app.delete("/delete_trade/{trade_id}")
def delete_trade(trade_id: int,
                 username: str = Depends(get_sub_from_jwt),
                 db: Session = Depends(get_main_db)):
    
    # Get the trade
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.username == username
    ).first()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Check if trade is already processed
    if trade.flag != "unprocessed":
        raise HTTPException(status_code=400, detail="Cannot delete processed trades")
    
    try:
        if trade.action == "buy":
            # Refund the user's balance
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            total_cost = Decimal(str(trade.quantity * trade.price))
            user.balance += total_cost
            
        elif trade.action == "sell":
            # Return shares to portfolio
            holding = db.query(Portfolio).filter(
                Portfolio.username == username,
                Portfolio.symbol == trade.symbol
            ).first()
            
            if holding:
                # Update existing holding
                holding.quantity += trade.quantity
                # Recalculate average price
                total_value = (Decimal(str(holding.price)) * Decimal(str(holding.quantity - trade.quantity)) + 
                             Decimal(str(trade.price)) * Decimal(str(trade.quantity)))
                holding.price = total_value / Decimal(str(holding.quantity))
            else:
                # Create new holding
                holding = Portfolio(
                    username=username,
                    symbol=trade.symbol,
                    quantity=trade.quantity,
                    price=Decimal(str(trade.price))
                )
                db.add(holding)
        
        # Delete the trade
        db.delete(trade)
        db.commit()
        
    except Exception as e:
        print(f"[db_interaction/delete_trade] Error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete trade")
    
    return {"msg": "Trade deleted successfully"}


@app.get("/get_portfolio", response_model=List[PortfolioItem])
def get_portfolio(username: str = Depends(get_sub_from_jwt),
                  db: Session = Depends(get_main_db)):
    
    return db.query(Portfolio).filter(Portfolio.username == username).all()


