class IBApp(EWrapper, EClient):

  def __init__(self):
        EClient.__init__(self, self)

        self.orders = {}
        self.positions = {}
      
  def position(self, account, contract, position, avgCost):
  
      self.positions[contract.symbol] = {
          "account": account,
          "qty": position,
          "avgCost": avgCost
      }

  def openOrder(self, orderId, contract, order, orderState):
  
      self.orders[orderId] = {
          "symbol": contract.symbol,
          "action": order.action,
          "qty": order.totalQuantity,
          "status": orderState.status,
          "filled": 0,
          "fills": []
              }


  def orderStatus(self, orderId, status, filled, remaining,
                avgFillPrice, *args):

    if orderId in self.orders:
        self.orders[orderId]["status"] = status
        self.orders[orderId]["filled"] = filled
        self.orders[orderId]["remaining"] = remaining

  def execDetails(self, reqId, contract, execution):
  
      orderId = execution.orderId
  
      if orderId not in self.orders:
          self.orders[orderId] = {}
  
      if "fills" not in self.orders[orderId]:
          self.orders[orderId]["fills"] = []
  
      self.orders[orderId]["fills"].append({
          "price": execution.price,
          "qty": execution.shares,
          "side": execution.side,
          "time": execution.time
      })

  def check_sync(self):

    for symbol, pos in self.positions.items():

        total_from_orders = 0

        for order in self.orders.values():
            if order.get("symbol") == symbol:

                for fill in order.get("fills", []):
                    if fill["side"] == "BUY":
                        total_from_orders += fill["qty"]
                    elif fill["side"] == "SELL":
                        total_from_orders -= fill["qty"]

        if total_from_orders != pos["qty"]:
            print(f"⚠️ DESCUADRE en {symbol}")
        else:
            print(f"✅ OK {symbol}")
