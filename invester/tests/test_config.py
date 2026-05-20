"""
Unit tests for config.py — Config class and static data catalogs.
"""
import pytest
from config import Config


class TestConfigBasics:
    """Test basic configuration values."""

    def test_secret_key_exists(self):
        assert Config.SECRET_KEY is not None
        assert len(Config.SECRET_KEY) > 0

    def test_sqlalchemy_uri_format(self):
        uri = Config.SQLALCHEMY_DATABASE_URI
        assert 'mysql+pymysql' in uri or 'sqlite' in uri

    def test_cache_ttl_positive(self):
        assert Config.CACHE_TTL > 0

    def test_model_dir_path(self):
        assert Config.MODEL_DIR is not None
        assert 'trained' in Config.MODEL_DIR

    def test_training_period_set(self):
        assert Config.TRAINING_PERIOD in ('1y', '2y', '3y', '5y')

    def test_prediction_features_list(self):
        assert isinstance(Config.PREDICTION_FEATURES, list)
        assert len(Config.PREDICTION_FEATURES) > 0
        assert 'RSI' in Config.PREDICTION_FEATURES
        assert 'MACD' in Config.PREDICTION_FEATURES


class TestNifty50Symbols:
    """Validate NIFTY50 symbol list."""

    def test_symbol_count(self):
        assert len(Config.NIFTY50_SYMBOLS) == 50

    def test_all_symbols_have_ns_suffix(self):
        for sym in Config.NIFTY50_SYMBOLS:
            assert sym.endswith('.NS'), f"{sym} missing .NS suffix"

    def test_key_stocks_present(self):
        expected = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'SBIN.NS']
        for sym in expected:
            assert sym in Config.NIFTY50_SYMBOLS, f"{sym} missing from NIFTY50"


class TestIndices:
    """Validate market indices mapping."""

    def test_indices_dict_not_empty(self):
        assert len(Config.INDICES) >= 3

    def test_nifty50_index_symbol(self):
        assert Config.INDICES['NIFTY50'] == '^NSEI'

    def test_sensex_index_symbol(self):
        assert Config.INDICES['SENSEX'] == '^BSESN'


class TestRiskProfiles:
    """Validate risk profile allocations."""

    def test_all_risk_levels_present(self):
        expected = ['conservative', 'moderate', 'aggressive', 'very_aggressive']
        for level in expected:
            assert level in Config.RISK_PROFILES

    def test_allocations_sum_to_100(self):
        for level, alloc in Config.RISK_PROFILES.items():
            total = sum(alloc.values())
            assert total == 100, f"{level} sums to {total}, expected 100"

    def test_all_categories_in_each_profile(self):
        categories = {'stocks', 'mutual_funds', 'gold', 'bonds', 'fd'}
        for level, alloc in Config.RISK_PROFILES.items():
            assert set(alloc.keys()) == categories, f"{level} has wrong categories"

    def test_aggressive_has_more_stocks_than_conservative(self):
        assert Config.RISK_PROFILES['aggressive']['stocks'] > Config.RISK_PROFILES['conservative']['stocks']

    def test_conservative_has_more_bonds_than_aggressive(self):
        assert Config.RISK_PROFILES['conservative']['bonds'] > Config.RISK_PROFILES['aggressive']['bonds']


class TestInvestmentTypes:
    """Validate investment type display names."""

    def test_all_categories_have_display_names(self):
        categories = ['stocks', 'mutual_funds', 'gold', 'bonds', 'fd']
        for cat in categories:
            assert cat in Config.INVESTMENT_TYPES
            assert len(Config.INVESTMENT_TYPES[cat]) > 0


class TestFDRates:
    """Validate fixed deposit rate catalog."""

    def test_fd_rates_not_empty(self):
        assert len(Config.FD_RATES) >= 4

    def test_each_bank_has_required_tenures(self):
        for bank, rates in Config.FD_RATES.items():
            for tenure in ('1yr', '2yr', '3yr', '5yr'):
                assert tenure in rates, f"{bank} missing {tenure}"
                assert rates[tenure] > 0, f"{bank} {tenure} rate should be > 0"

    def test_each_bank_has_min_deposit(self):
        for bank, rates in Config.FD_RATES.items():
            assert 'min_deposit' in rates
            assert rates['min_deposit'] > 0

    def test_senior_extra_non_negative(self):
        for bank, rates in Config.FD_RATES.items():
            assert rates.get('senior_extra', 0) >= 0


class TestBondsCatalog:
    """Validate bonds catalog."""

    def test_bonds_catalog_not_empty(self):
        assert len(Config.BONDS_CATALOG) >= 4

    def test_each_bond_has_yield(self):
        for name, info in Config.BONDS_CATALOG.items():
            assert 'yield' in info, f"{name} missing yield"
            assert info['yield'] > 0

    def test_each_bond_has_required_fields(self):
        required = ['yield', 'type', 'risk', 'tenure', 'min_investment']
        for name, info in Config.BONDS_CATALOG.items():
            for field in required:
                assert field in info, f"{name} missing {field}"

    def test_government_bonds_exist(self):
        gov_bonds = [n for n, i in Config.BONDS_CATALOG.items() if i['type'] == 'Government']
        assert len(gov_bonds) >= 2


class TestMutualFundsCatalog:
    """Validate mutual funds catalog."""

    def test_mf_catalog_not_empty(self):
        assert len(Config.MUTUAL_FUNDS_CATALOG) >= 10

    def test_each_fund_has_required_fields(self):
        required = ['category', 'type', 'risk', 'returns_1y', 'returns_3y',
                     'expense_ratio', 'min_sip', 'min_lumpsum']
        for name, info in Config.MUTUAL_FUNDS_CATALOG.items():
            for field in required:
                assert field in info, f"MF '{name}' missing {field}"

    def test_expense_ratios_reasonable(self):
        for name, info in Config.MUTUAL_FUNDS_CATALOG.items():
            assert 0 < info['expense_ratio'] < 2.0, f"{name} expense ratio out of range"

    def test_risk_levels_valid(self):
        valid = {'Very Low', 'Low', 'Low-Moderate', 'Moderate', 'Moderate-High', 'High', 'Very High'}
        for name, info in Config.MUTUAL_FUNDS_CATALOG.items():
            assert info['risk'] in valid, f"{name} has invalid risk '{info['risk']}'"


class TestMetalsCatalog:
    """Validate precious metals catalog."""

    def test_metals_catalog_not_empty(self):
        assert len(Config.METALS_CATALOG) >= 3

    def test_each_metal_has_required_fields(self):
        required = ['type', 'risk', 'returns_1y', 'returns_3y', 'min_investment']
        for name, info in Config.METALS_CATALOG.items():
            for field in required:
                assert field in info, f"Metal '{name}' missing {field}"

    def test_sgb_present(self):
        sgb = [n for n in Config.METALS_CATALOG if 'SGB' in n or 'Sovereign' in n]
        assert len(sgb) >= 1
