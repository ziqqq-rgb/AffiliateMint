# backend/app/services/affiliate_link.py
"""Appends the Shopee affiliate buy link to generated copy.
TikTok Shop videos already get a shoppable product tag from the
platform itself - only Shopee needs the link written into the text,
since Threads has no equivalent tagging feature."""
from app.models import Platform, ScrapedProduct

BUY_LINK_LABEL = "Beli sekarang di sini"  # "Buy now here"


def append_buy_link(text: str, product: ScrapedProduct) -> str:
    if product.platform != Platform.SHOPEE or not product.affiliate_link:
        return text
    return f"{text}\n\n{BUY_LINK_LABEL}: {product.affiliate_link}"