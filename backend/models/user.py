from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, CHAR_LENGTH, GUID


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    email = Column(String(CHAR_LENGTH), unique=True,
                   index=True, nullable=False)
    firstname = Column(String(CHAR_LENGTH), nullable=False)
    lastname = Column(String(CHAR_LENGTH), nullable=False)
    hashed_password = Column(String(CHAR_LENGTH), nullable=False)
    role = Column(String(50), default="Customer")  # Customer, Supplier, Admin
    verified = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(CHAR_LENGTH), nullable=True, unique=True) # NEW: Store Stripe Customer ID
    
    # Profile fields
    age = Column(String(10), nullable=True)
    gender = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    timezone = Column(String(100), nullable=True)
    
    # Verification fields
    verification_token = Column(String(255), nullable=True)
    token_expiration = Column(DateTime(timezone=True), nullable=True)

    # Relationships with lazy loading
    addresses = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    orders = relationship("Order", back_populates="user", lazy="selectin")
    reviews = relationship("Review", back_populates="user", lazy="selectin")
    wishlists = relationship(
        "Wishlist", back_populates="user", lazy="selectin")
    blog_posts = relationship(
        "BlogPost", back_populates="author", lazy="selectin")
    subscriptions = relationship(
        "Subscription", back_populates="user", lazy="selectin")
    payment_methods = relationship(
        "PaymentMethod", back_populates="user", lazy="selectin")
    transactions = relationship(
        "Transaction", back_populates="user", lazy="selectin")
    supplied_products = relationship(
        "Product", back_populates="supplier", lazy="selectin")
    notifications = relationship(
        "Notification", back_populates="user", lazy="selectin")
    activity_logs = relationship(
        "ActivityLog", back_populates="user", lazy="selectin")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan", lazy="selectin")
    # negotiations_as_buyer = relationship(
    #     "Negotiation", foreign_keys="Negotiation.buyer_id", back_populates="buyer"
    # )
    # negotiations_as_seller = relationship(
    #     "Negotiation", foreign_keys="Negotiation.seller_id", back_populates="seller"
    # )
    
    # Enhanced payment and loyalty relationships
    payment_intents = relationship(
        "PaymentIntent", back_populates="user", lazy="selectin")
    loyalty_account = relationship(
        "LoyaltyAccount", back_populates="user", uselist=False, lazy="selectin")
    notification_preferences = relationship(
        "NotificationPreference", back_populates="user", uselist=False, lazy="selectin")

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.firstname} {self.lastname}"

    @property
    def default_address(self):
        """Get user's default address"""
        return next((addr for addr in self.addresses if addr.is_default), None)

    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses"""
        return {
            "id": str(self.id),
            "email": self.email,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "full_name": self.full_name,
            "role": self.role,
            "verified": self.verified,
            "active": self.active,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Address(BaseModel):
    __tablename__ = "addresses"
    __table_args__ = {'extend_existing': True}

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    street = Column(String(CHAR_LENGTH), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    post_code = Column(String(20), nullable=False)
    kind = Column(String(50), default="Shipping")  # Shipping, Billing
    is_default = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="addresses")

    def to_dict(self) -> dict:
        """Convert address to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "post_code": self.post_code,
            "kind": self.kind,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
