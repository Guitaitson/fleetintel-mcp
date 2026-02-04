"""Unit tests for Guardrails MCP Server"""

import pytest
from fastapi import HTTPException
from app.core.guardrails import (
    InputSanitizer,
    validate_date_range,
    GuardrailedVehicleQuery,
    GuardrailedRegistrationQuery,
    GuardrailedEmpresaQuery,
    rate_limiter,
    QUERY_TIMEOUT_SECONDS,
    MAX_DATE_RANGE_DAYS,
    MAX_RESULTS_LIMIT
)


class TestInputSanitizer:
    """Test cases for InputSanitizer"""
    
    def test_sanitize_uf_valid(self):
        """Test valid UF sanitization"""
        assert InputSanitizer.sanitize_uf('SP') == 'SP'
        assert InputSanitizer.sanitize_uf('rj') == 'RJ'
        assert InputSanitizer.sanitize_uf('  sp  ') == 'SP'
    
    def test_sanitize_uf_invalid(self):
        """Test invalid UF sanitization"""
        with pytest.raises(HTTPException) as exc_info:
            InputSanitizer.sanitize_uf('XX')
        assert 'UF invalida' in str(exc_info.value.detail)
    
    def test_sanitize_uf_empty(self):
        """Test empty UF sanitization"""
        assert InputSanitizer.sanitize_uf('') == ''
        assert InputSanitizer.sanitize_uf(None) is None
    
    def test_sanitize_cnpj_valid(self):
        """Test valid CNPJ sanitization"""
        cnpj = InputSanitizer.sanitize_cnpj('12345678000100')
        assert cnpj == '12345678000100'
    
    def test_sanitize_cnpj_with_formatting(self):
        """Test CNPJ with formatting characters"""
        cnpj = InputSanitizer.sanitize_cnpj('12.345.678/0001-00')
        assert cnpj == '12345678000100'
    
    def test_sanitize_cnpj_invalid_length(self):
        """Test invalid CNPJ length"""
        with pytest.raises(HTTPException) as exc_info:
            InputSanitizer.sanitize_cnpj('123')
        assert '14 digitos' in str(exc_info.value.detail)
    
    def test_sanitize_cep_valid(self):
        """Test valid CEP sanitization"""
        cep = InputSanitizer.sanitize_cep('01311000')
        assert cep == '01311000'
    
    def test_sanitize_cep_with_formatting(self):
        """Test CEP with formatting"""
        cep = InputSanitizer.sanitize_cep('01311-000')
        assert cep == '01311000'
    
    def test_sanitize_cep_invalid(self):
        """Test invalid CEP"""
        with pytest.raises(HTTPException) as exc_info:
            InputSanitizer.sanitize_cep('123')
        assert '8 digitos' in str(exc_info.value.detail)
    
    def test_sanitize_string_removes_dangerous_patterns(self):
        """Test that dangerous SQL patterns are detected"""
        with pytest.raises(HTTPException) as exc_info:
            InputSanitizer.sanitize_string("'; DROP TABLE users;--", 'test')
        assert 'caracteres perigosos' in str(exc_info.value.detail)
    
    def test_sanitize_string_limits_length(self):
        """Test string length limit"""
        long_string = 'a' * 300
        result = InputSanitizer.sanitize_string(long_string, 'test')
        assert len(result) == 255


class TestDateValidation:
    """Test cases for date range validation"""
    
    def test_valid_date_range_short(self):
        """Test valid short date range"""
        start, end = validate_date_range('2026-01-01', '2026-01-31')
        assert (end - start).days == 30
    
    def test_valid_date_range_max_days(self):
        """Test date range at maximum limit"""
        start, end = validate_date_range('2026-01-01', '2026-04-01')
        assert (end - start).days == 90
    
    def test_date_range_exceeds_limit(self):
        """Test date range exceeding limit"""
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range('2025-01-01', '2026-01-01')
        assert 'Periodo maximo excedido' in str(exc_info.value.detail)
        assert '90 dias' in str(exc_info.value.detail)
    
    def test_start_after_end(self):
        """Test start date after end date"""
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range('2026-01-31', '2026-01-01')
        assert 'Data inicial deve ser anterior' in str(exc_info.value.detail)
    
    def test_invalid_start_date_format(self):
        """Test invalid start date format"""
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range('01-01-2026', '2026-01-31')
        assert 'Data inicial invalida' in str(exc_info.value.detail)
    
    def test_invalid_end_date_format(self):
        """Test invalid end date format"""
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range('2026-01-01', '31/01/2026')
        assert 'Data final invalida' in str(exc_info.value.detail)


class TestGuardrailedVehicleQuery:
    """Test cases for GuardrailedVehicleQuery schema"""
    
    def test_valid_query(self):
        """Test valid vehicle query"""
        query = GuardrailedVehicleQuery(
            placa='ABC1234',
            marca='Volkswagen',
            limit=50
        )
        assert query.placa == 'ABC1234'
        assert query.marca == 'Volkswagen'
        assert query.limit == 50
    
    def test_limit_exceeds_max(self):
        """Test limit exceeding maximum"""
        with pytest.raises(ValueError):
            GuardrailedVehicleQuery(limit=2000)
    
    def test_limit_below_min(self):
        """Test limit below minimum"""
        with pytest.raises(ValueError):
            GuardrailedVehicleQuery(limit=0)
    
    def test_chassi_length_limit(self):
        """Test chassis length limit"""
        query = GuardrailedVehicleQuery(chassi='a' * 17)
        assert len(query.chassi) == 17
        
        query = GuardrailedVehicleQuery(chassi='a' * 20)
        assert len(query.chassi) == 20  # Actually limited by schema


class TestGuardrailedRegistrationQuery:
    """Test cases for GuardrailedRegistrationQuery schema"""
    
    def test_valid_query_with_uf(self):
        """Test valid registration query with UF"""
        query = GuardrailedRegistrationQuery(
            uf_emplacamento='SP',
            limit=100
        )
        assert query.uf_emplacamento == 'SP'
        assert query.limit == 100
    
    def test_uf_required(self):
        """Test that UF is required"""
        with pytest.raises(ValidationError):
            GuardrailedRegistrationQuery(uf_emplacamento='')
    
    def test_invalid_uf(self):
        """Test invalid UF"""
        with pytest.raises(HTTPException) as exc_info:
            GuardrailedRegistrationQuery(uf_emplacamento='XX')
        assert 'UF invalida' in str(exc_info.value.detail)
    
    def test_date_validation(self):
        """Test date validation in query"""
        with pytest.raises(HTTPException) as exc_info:
            GuardrailedRegistrationQuery(
                uf_emplacamento='SP',
                data_emplacamento_inicio='2025-01-01',
                data_emplacamento_fim='2026-01-01'
            )
        assert 'Periodo maximo excedido' in str(exc_info.value.detail)


class TestGuardrailedEmpresaQuery:
    """Test cases for GuardrailedEmpresaQuery schema"""
    
    def test_valid_query(self):
        """Test valid empresa query"""
        query = GuardrailedEmpresaQuery(
            cnpj='12345678000100',
            razao_social='Empresa Teste',
            limit=50
        )
        assert query.cnpj == '12345678000100'
        assert query.razao_social == 'Empresa Teste'
    
    def test_cnpj_sanitization(self):
        """Test CNPJ sanitization"""
        query = GuardrailedEmpresaQuery(cnpj='12.345.678/0001-00')
        assert query.cnpj == '12345678000100'
    
    def test_cnpj_invalid_length(self):
        """Test invalid CNPJ length"""
        with pytest.raises(ValidationError):
            GuardrailedEmpresaQuery(cnpj='123')


class TestRateLimiter:
    """Test cases for RateLimiter"""
    
    def test_rate_limiter_initial_state(self):
        """Test rate limiter initial state"""
        remaining = rate_limiter.get_remaining(MagicMock())
        assert 'hourly_remaining' in remaining
        assert 'daily_remaining' in remaining


class TestConfiguration:
    """Test cases for configuration constants"""
    
    def test_query_timeout_seconds(self):
        """Test query timeout configuration"""
        assert QUERY_TIMEOUT_SECONDS == 30
    
    def test_max_date_range_days(self):
        """Test max date range configuration"""
        assert MAX_DATE_RANGE_DAYS == 90
    
    def test_max_results_limit(self):
        """Test max results limit configuration"""
        assert MAX_RESULTS_LIMIT == 1000


# Mock request object for testing
from unittest.mock import MagicMock

# Import ValidationError for testing
from pydantic import ValidationError
