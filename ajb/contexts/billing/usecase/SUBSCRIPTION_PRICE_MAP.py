import os

from ..billing_models import SubscriptionPlan

APP_SUMO_PRICE_ID = os.getenv("APP_SUMO_PRICE_ID", "price_1PSmTMDd0dqh9J6nKDa2buRV")
SILVER_TIER_PRICE_ID = os.getenv(
    "SILVER_TIER_PRICE_ID", "price_1PSmOVDd0dqh9J6nPqTZWjG5"
)
GOLD_TIER_PRICE_ID = os.getenv("GOLD_TIER_PRICE_ID", "price_1PSmOwDd0dqh9J6nisDSnpYZ")
PLATINUM_TIER_PRICE_ID = os.getenv(
    "PLATINUM_TIER_PRICE_ID", "price_1PSmPHDd0dqh9J6nF16RWPbC"
)


SUBSCRIPTION_PRICE_MAP: dict[SubscriptionPlan, str] = {
    SubscriptionPlan.APPSUMO: APP_SUMO_PRICE_ID,
    SubscriptionPlan.SILVER: SILVER_TIER_PRICE_ID,
    SubscriptionPlan.GOLD: GOLD_TIER_PRICE_ID,
    SubscriptionPlan.PLATINUM: PLATINUM_TIER_PRICE_ID,
}
