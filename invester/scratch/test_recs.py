"""Quick test of the enhanced recommendation engine"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.recommendation import _build_mf_recs, _build_metal_recs, _build_bond_recs, _build_fd_recs
import json

amount = 100000

print("=" * 60)
print("MUTUAL FUNDS (Moderate, Medium Horizon)")
print("=" * 60)
mf = _build_mf_recs(30000, 'moderate', 'medium')
for r in mf:
    print(f"  {r['name']:30s} | ₹{r['amount']:>8,.0f} | {r['returns_1y']}% 1Y | {r['returns_3y']}% 3Y | {r['category']}")

print("\n" + "=" * 60)
print("GOLD & METALS (Moderate, Medium Horizon)")
print("=" * 60)
metals = _build_metal_recs(10000, 'moderate', 'medium')
for r in metals:
    print(f"  {r['name']:30s} | ₹{r['amount']:>8,.0f} | {r['returns_1y']}% 1Y | {r['type']}")

print("\n" + "=" * 60)
print("BONDS (Moderate, Medium Horizon)")
print("=" * 60)
bonds = _build_bond_recs(15000, 'moderate', 'medium')
for r in bonds:
    print(f"  {r['name']:30s} | ₹{r['amount']:>8,.0f} | {r['yield']}% yield | {r['type']}")

print("\n" + "=" * 60)
print("FIXED DEPOSITS (Moderate, Medium Horizon)")
print("=" * 60)
fds = _build_fd_recs(10000, 'moderate', 'medium')
for r in fds:
    print(f"  {r['name']:30s} | ₹{r['amount']:>8,.0f} | {r['rate']}% rate | Maturity: ₹{r['maturity_amount']:,.0f}")

print("\n✅ All 4 categories generated successfully!")
