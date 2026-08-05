export function formatRM(amount: number): string {
  return `RM${amount.toFixed(2)}`;
}

/** Whole-ringgit prices (subscription plans) read cleaner without cents -
 * "RM89" instead of "RM89.00". Product prices still use formatRM above. */
export function formatRMWhole(amount: number): string {
  return `RM${amount.toFixed(0)}`;
}
