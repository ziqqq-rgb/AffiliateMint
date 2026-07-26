import type { CardStatus, ContentCard } from "../types";
import { STATUS_ORDER } from "./statusMeta";

export function isResearched(status: CardStatus): boolean {
  return STATUS_ORDER.indexOf(status) > STATUS_ORDER.indexOf("scraped");
}

export function isPosted(card: ContentCard): boolean {
  return card.posted_at !== null;
}