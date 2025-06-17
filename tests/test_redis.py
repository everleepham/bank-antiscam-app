import pytest
from unittest.mock import patch, MagicMock
from app.models.redis_model import RedisTrustScoreModel
from app.services.redis_service import RedisTrustScoreService  



def test_get_score_success(service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=b'42'):
        score = service.get_score('user_1')
        assert score == 42

def test_get_score_none(service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=None):
        score = service.get_score('user_1')
        assert score is None

def test_get_score_invalid_value(service, caplog):
    with patch.object(RedisTrustScoreModel, 'get', return_value=b'not_a_number'):
        with caplog.at_level('WARNING'):
            score = service.get_score('user_1')
            assert score is None
            assert "Failed to convert Redis trust score" in caplog.text

def test_set_score(service):
    with patch.object(RedisTrustScoreModel, 'set', return_value=True) as mock_set:
        result = service.set_score('user_1', 55)
        mock_set.assert_called_once_with('user_1', '55', 1800)
        assert result is True

def test_has_score_true(service):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=1):
        assert service.has_score('user_1') is True

def test_has_score_false(service):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=0):
        assert service.has_score('user_1') is False

def test_update_score_success(service):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=1), \
        patch.object(RedisTrustScoreModel, 'set', return_value=True) as mock_set:
        result = service.update_score('user_1', 99)
        mock_set.assert_called_once_with('user_1', '99', 3600)
        assert result is True

def test_update_score_no_existing(service, caplog):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=0):
        with caplog.at_level('WARNING'):
            result = service.update_score('user_1', 99)
            assert result is False
            assert "Attempted to update score for user" in caplog.text

def test_get_or_load_score_existing(service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=b'15'):
        result = service.get_or_load_score('user_1', lambda x: 100)
        assert result == 15

def test_get_or_load_score_load_and_set(service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=None), \
        patch.object(RedisTrustScoreModel, 'set', return_value=True) as mock_set:
        loader = lambda user_id: 200
        result = service.get_or_load_score('user_1', loader)
        mock_set.assert_called_once_with('user_1', '200', 3600)
        assert result == 200

def test_get_or_load_score_load_none(service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=None):
        loader = lambda user_id: None
        result = service.get_or_load_score('user_1', loader)
        assert result == 0
