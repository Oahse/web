"""
This module implements a simple negotiation algorithm simulating offers and counter-offers
between a buyer and a seller. It's designed to be integrated into an e-commerce platform
where prices can be negotiated.
"""

class NegotiationAgent:
    """
    Base class for a negotiating entity (Buyer or Seller).
    Defines core properties and behaviors common to both.
    """
    def __init__(self, name: str, target_price: float, limit_price: float, style: str = "balanced"):
        """
        Initializes a NegotiationAgent.
        :param name: Identifier for the agent.
        :param target_price: The agent's initial or current desired price.
        :param limit_price: The agent's absolute acceptable price boundary (e.g., max for buyer, min for seller).
        :param style: Defines the agent's negotiation behavior (e.g., "aggressive", "patient").
        """
        self.name = name
        self.target = target_price
        self.limit = limit_price
        self.style = style

    def concession_rate(self) -> float:
        """
        Determines the rate at which the agent is willing to concede its offer.
        This rate influences how quickly the agent moves towards the other party's price.
        """
        if self.style == "aggressive":
            return 0.02  # Concedes very little
        if self.style == "patient":
            return 0.05
        if self.style == "friendly":
            return 0.10 # Concedes more
        return 0.05 # Default for "balanced" or unrecognized styles

    def update_target(self, new_price: float):
        """
        Dynamically updates the agent’s current offer target.
        This is typically used in a continuous negotiation to adjust the agent's stance.
        """
        self.target = new_price

    def set_price(self, new_price: float):
        """
        Allows an external interface (e.g., UI) to directly set a new round price for the agent.
        """
        self.target = new_price
    
    def to_dict(self) -> dict:
        """Serializes the NegotiationAgent's state to a dictionary."""
        return {
            "name": self.name,
            "target": self.target,
            "limit": self.limit,
            "style": self.style,
            "agent_type": self.__class__.__name__ # To differentiate Buyer/Seller upon deserialization
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Deserializes a dictionary back into a NegotiationAgent instance.
        This method is meant to be overridden by subclasses (Buyer/Seller) to instantiate
        the correct specific agent type.
        """
        return cls(data["name"], float(data["target"]), float(data["limit"]), data["style"])


class Buyer(NegotiationAgent):
    """
    Represents the buyer in the negotiation.
    The buyer aims to decrease the price and will make offers towards the seller's target.
    """
    def make_offer(self, seller_offer: float) -> float:
        """
        Calculates the buyer's next offer based on the seller's last offer.
        The buyer moves their offer towards the seller's price, limited by their own maximum acceptable price.
        :param seller_offer: The last offer made by the seller.
        :return: The buyer's new calculated offer.
        """
        # Calculate how much the buyer should move their offer
        # The move is proportional to the difference between seller's offer and buyer's target,
        # scaled by the buyer's concession rate.
        # Ensure both values are floats to handle any serialization issues
        seller_offer = float(seller_offer)
        target = float(self.target)
        move = (seller_offer - target) * self.concession_rate()
        
        # The new offer is the current target plus the calculated move.
        offer = target + move
        
        # Ensure the buyer's offer does not exceed their limit price (max price they are willing to pay).
        return min(offer, float(self.limit))

    @classmethod
    def from_dict(cls, data: dict):
        """Deserializes a dictionary back into a Buyer instance."""
        return cls(data["name"], float(data["target"]), float(data["limit"]), data["style"])


class Seller(NegotiationAgent):
    """
    Represents the seller in the negotiation.
    The seller aims to maintain a higher price and will make counter-offers towards the buyer's offer.
    """
    def counter_offer(self, buyer_offer: float) -> float:
        """
        Calculates the seller's next counter-offer based on the buyer's last offer.
        The seller moves their offer towards the buyer's price, limited by their own minimum acceptable price.
        :param buyer_offer: The last offer made by the buyer.
        :return: The seller's new calculated counter-offer.
        """
        # Calculate how much the seller should move their counter-offer
        # The move is proportional to the difference between seller's target and buyer's offer,
        # scaled by the seller's concession rate.
        # Ensure both values are floats to handle any serialization issues
        buyer_offer = float(buyer_offer)
        target = float(self.target)
        limit = float(self.limit)
        move = (target - buyer_offer) * self.concession_rate()
        
        # The new counter-offer is the current target minus the calculated move.
        offer = target - move
        
        # Ensure the seller's offer does not go below their limit price (minimum price they are willing to accept).
        return max(offer, limit)

    @classmethod
    def from_dict(cls, data: dict):
        """Deserializes a dictionary back into a Seller instance."""
        return cls(data["name"], float(data["target"]), float(data["limit"]), data["style"])


class NegotiationEngine:
    """
    Manages the overall negotiation process between a Buyer and a Seller.
    It runs the negotiation round by round, checking for deal closure.
    """
    def __init__(self, buyer: Buyer, seller: Seller):
        """
        Initializes the NegotiationEngine.
        :param buyer: The Buyer agent participating in the negotiation.
        :param seller: The Seller agent participating in the negotiation.
        """
        self.buyer = buyer
        self.seller = seller
        self.round = 0          # Tracks the current negotiation round
        self.finished = False   # True if a deal has been reached
        self.final_price = None # Stores the agreed price once negotiation concludes

    def check_closure(self, buyer_offer: float, seller_offer: float) -> bool:
        """
        Determines if a deal can be closed.
        A deal is reached if the buyer's offer is greater than or equal to the seller's offer.
        :param buyer_offer: The current offer from the buyer.
        :param seller_offer: The current offer from the seller.
        :return: True if a deal can be made, False otherwise.
        """
        if buyer_offer < self.seller.limit: # Buyer's offer must be at least seller's limit
            return False
        return buyer_offer >= seller_offer

    def step(self) -> dict:
        """
        Executes ONE round of negotiation.
        This method should be called repeatedly by the UI or an external process
        until the negotiation is finished.
        :return: A dictionary containing the current state of the negotiation,
                 including offers, round number, and if a deal was reached.
        """

        if self.finished:
            # If negotiation already finished, return the final result.
            return {
                "message": "Negotiation already finished.",
                "final_price": self.final_price,
                "round": self.round,
                "finished": True
            }

        self.round += 1  # Increment round counter for each step

        # --- Buyer's Turn ---
        # Buyer makes an offer based on the seller's current target.
        buyer_offer = self.buyer.make_offer(self.seller.target)

        # Check for immediate closure after buyer's offer.
        # This handles cases where the buyer's new offer meets or exceeds the seller's current target.
        if self.check_closure(buyer_offer, self.seller.target):
            self.finished = True
            self.final_price = round(buyer_offer, 2)
            return {
                "message": f"Deal reached at ₦{self.final_price:.2f}",
                "final_price": self.final_price,
                "round": self.round,
                "finished": True
            }

        # --- Seller's Turn ---
        # Seller makes a counter-offer based on the buyer's last offer.
        seller_offer = self.seller.counter_offer(buyer_offer)

        # Check for closure after seller's counter-offer.
        # This handles cases where the buyer's offer (from this round) meets or exceeds the seller's new counter-offer.
        if self.check_closure(buyer_offer, seller_offer):
            self.finished = True
            self.final_price = round(seller_offer, 2)
            return {
                "message": f"Deal reached at ₦{self.final_price:.2f}",
                "final_price": self.final_price,
                "round": self.round,
                "finished": True
            }

        # --- No Closure Yet ---
        # If no deal is reached in this round, return the current offers and state.
        return {
            "message": f"Round {self.round} complete.",
            "buyer_offer": round(buyer_offer, 2), # Corrected to return current offers for ongoing state
            "seller_offer": round(seller_offer, 2), # Corrected to return current offers for ongoing state
            "round": self.round,
            "finished": False
        }
    
    def to_dict(self) -> dict:
        """Serializes the NegotiationEngine's state to a dictionary for persistence."""
        return {
            "buyer": self.buyer.to_dict(),
            "seller": self.seller.to_dict(),
            "round": self.round,
            "finished": self.finished,
            "final_price": self.final_price,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserializes a dictionary back into a NegotiationEngine instance."""
        buyer_data = data["buyer"]
        seller_data = data["seller"]

        # Instantiate Buyer/Seller from their dict representations using their specific from_dict
        buyer = Buyer.from_dict(buyer_data)
        seller = Seller.from_dict(seller_data)

        engine = cls(buyer, seller)
        engine.round = data["round"]
        engine.finished = data["finished"]
        engine.final_price = data["final_price"]
        return engine
