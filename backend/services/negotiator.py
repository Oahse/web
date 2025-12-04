class NegotiationAgent:
    def __init__(self, name, target_price, limit_price, style="balanced"):
        self.name = name
        self.target = target_price
        self.limit = limit_price
        self.style = style

    def concession_rate(self):
        if self.style == "aggressive":
            return 0.02
        if self.style == "patient":
            return 0.05
        if self.style == "friendly":
            return 0.10
        return 0.05

    def update_target(self, new_price):
        """Dynamically update the agent’s current offer target."""
        self.target = new_price

    def set_price(self, new_price):
        """UI can directly set a new round price."""
        self.target = new_price


class Buyer(NegotiationAgent):
    def make_offer(self, seller_offer):
        move = (seller_offer - self.target) * self.concession_rate()
        offer = self.target + move
        return min(offer, self.limit)


class Seller(NegotiationAgent):
    def counter_offer(self, buyer_offer):
        move = (self.target - buyer_offer) * self.concession_rate()
        offer = self.target - move
        return max(offer, self.limit)


class NegotiationEngine:
    def __init__(self, buyer, seller):
        self.buyer = buyer
        self.seller = seller
        self.round = 0
        self.finished = False
        self.final_price = None

    def check_closure(self, buyer_offer, seller_offer):
        return buyer_offer >= seller_offer

    def step(self):
        """Runs ONE negotiation round only.
           UI should call this each time the user clicks 'Next Round'.
        """

        if self.finished:
            return {
                "message": "Negotiation already finished.",
                "final_price": self.final_price,
                "round": self.round,
                "finished": True
            }

        self.round += 1

        # Buyer makes offer
        buyer_offer = self.buyer.make_offer(self.seller.target)

        # Check for closure
        if self.check_closure(buyer_offer, self.seller.target):
            self.finished = True
            self.final_price = round(buyer_offer, 2)
            return {
                "message": f"Deal reached at {self.final_price:.2f}",
                "final_price": self.final_price,
                "round": self.round,
                "finished": True
            }

        # Seller makes counter-offer
        seller_offer = self.seller.counter_offer(buyer_offer)

        if self.check_closure(buyer_offer, seller_offer):
            self.finished = True
            self.final_price = round(seller_offer, 2)
            return {
                "message": f"Deal reached at {self.final_price:.2f}",
                "final_price": self.final_price,
                "round": self.round,
                "finished": True
            }

        # No closure yet — return current state
        return {
            "message": f"Round {self.round} complete.",
            "final_price": self.seller.target,
            "round": self.round,
            "finished": False
        }

# Example usage:

# buyer  = Buyer("Oscar", 10000, 20000, "friendly")
# seller = Seller("Market Woman", 30000, 18000, "friendly")

# engine = NegotiationEngine(buyer, seller)

# UI passes new values before stepping
# engine.buyer.set_price(new_buyer_price)
# engine.seller.set_price(new_seller_price)

# result = engine.step()

# print(result)
