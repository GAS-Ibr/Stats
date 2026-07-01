from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order


class IBApp(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        # Estado centralizado
        self.orders = {}
        self.positions = {}

        self.open_orders_end = False
        self.positions_end = False

    # =========================
    # CONEXIÓN
    # =========================

    def nextValidId(self, orderId: int):
        print("Conectado. NextValidId:", orderId)

        # Pedir estado inicial
        self.reqPositions()
        self.reqOpenOrders()

    # =========================
    # ÓRDENES
    # =========================

    def openOrder(self, orderId, contract, order, orderState):

        self.orders[orderId] = {
            "symbol": contract.symbol,
            "action": order.action,
            "qty": order.totalQuantity,
            "status": orderState.status,
            "filled": 0,
            "remaining": order.totalQuantity,
            "fills": []
        }

        print(f"[OPEN ORDER] {orderId} {contract.symbol} {order.action}")

    def openOrderEnd(self):
        print("== FIN ÓRDENES ==")
        self.open_orders_end = True
        self.check_ready()

    # =========================
    # ESTADO ORDEN
    # =========================

    def orderStatus(self, orderId, status, filled, remaining,
                    avgFillPrice, *args):

        if orderId in self.orders:
            self.orders[orderId]["status"] = status
            self.orders[orderId]["filled"] = filled
            self.orders[orderId]["remaining"] = remaining

        print(f"[STATUS] {orderId} {status} Filled:{filled}")

    # =========================
    # FILLS REALES
    # =========================

    def execDetails(self, reqId, contract, execution):

        orderId = execution.orderId
        symbol = contract.symbol

        if orderId not in self.orders:
            self.orders[orderId] = {
                "symbol": symbol,
                "fills": []
            }

        if "fills" not in self.orders[orderId]:
            self.orders[orderId]["fills"] = []

        fill = {
            "price": execution.price,
            "qty": execution.shares,
            "side": execution.side,
            "time": execution.time
        }

        self.orders[orderId]["fills"].append(fill)

        print(f"[FILL] {symbol} {execution.side} {execution.shares} @ {execution.price}")

        # 🔥 actualización inmediata de posiciones
        self.update_position_from_fill(symbol, execution)

    def execDetailsEnd(self, reqId):
        print("== FIN FILLS ==")

    # =========================
    # POSICIONES
    # =========================

    def position(self, account, contract, position, avgCost):

        self.positions[contract.symbol] = {
            "qty": position,
            "avgCost": avgCost
        }

        print(f"[POSITION] {contract.symbol} {position} @ {avgCost}")

    def positionEnd(self):
        print("== FIN POSICIONES ==")
        self.positions_end = True
        self.check_ready()

    # =========================
    # SINCRONIZACIÓN
    # =========================

    def check_ready(self):
        if self.open_orders_end and self.positions_end:
            print("\n✅ Estado inicial cargado\n")
            self.print_state()
            self.check_sync()

    def check_sync(self):

        print("\n🔍 Verificando sincronización...\n")

        for symbol, pos in self.positions.items():

            total = 0

            for order in self.orders.values():
                if order.get("symbol") == symbol:

                    for fill in order.get("fills", []):
                        if fill["side"] == "BUY":
                            total += fill["qty"]
                        elif fill["side"] == "SELL":
                            total -= fill["qty"]

            if total != pos["qty"]:
                print(f"⚠️ DESCUADRE {symbol}: IB={pos['qty']} vs FILLS={total}")
            else:
                print(f"✅ OK {symbol}")

    # =========================
    # UPDATE RÁPIDO POSICIÓN
    # =========================

    def update_position_from_fill(self, symbol, execution):

        if symbol not in self.positions:
            self.positions[symbol] = {"qty": 0, "avgCost": 0}

        if execution.side == "BUY":
            self.positions[symbol]["qty"] += execution.shares
        else:
            self.positions[symbol]["qty"] -= execution.shares

    # =========================
    # UTILIDADES
    # =========================

    def print_state(self):

        print("\n📊 POSICIONES:")
        for s, p in self.positions.items():
            print(s, p)

        print("\n📊 ÓRDENES:")
        for oid, o in self.orders.items():
            print(oid, o)


# =========================
# EJECUCIÓN
# =========================

def run():
    app = IBApp()
    app.connect("127.0.0.1", 7497, 1)
    app.run()


if __name__ == "__main__":
    run()
