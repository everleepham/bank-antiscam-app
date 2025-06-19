from unittest.mock import patch
from app.models.redis_model import RedisTrustScoreModel


# Test: get_score should return integer value when valid data exists
def test_get_score_success(redis_service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=b'42'):
        score = redis_service.get_score('user_1')
        assert score == 42

# Test: get_score should return None when no data exists
def test_get_score_none(redis_service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=None):
        score = redis_service.get_score('user_1')
        assert score is None

# Test: get_score should handle invalid data format and log a warning
def test_get_score_invalid_value(redis_service, caplog):
    with patch.object(RedisTrustScoreModel, 'get', return_value=b'not_a_number'):
        with caplog.at_level('WARNING'):
            score = redis_service.get_score('user_1')
            assert score is None
            assert "Failed to convert Redis trust score" in caplog.text

# Test: set_score should call Redis set with correct parameters and return True
def test_set_score(redis_service):
    with patch.object(RedisTrustScoreModel, 'set', return_value=True) as mock_set:
        result = redis_service.set_score('user_1', 55)
        mock_set.assert_called_once_with('user_1', '55', 3600)
        assert result is True

# Test: has_score should return True when Redis.exists returns 1
def test_has_score_true(redis_service):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=1):
        assert redis_service.has_score('user_1') == True

# Test: has_score should return False when Redis.exists returns 0
def test_has_score_false(redis_service):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=0):
        assert redis_service.has_score('user_1') == False

# Test: update_score should update score if key already exists
def test_update_score_success(redis_service):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=1), \
        patch.object(RedisTrustScoreModel, 'set', return_value=True) as mock_set:
        result = redis_service.update_score('user_1', 99)
        mock_set.assert_called_once_with('user_1', '99', 3600)
        assert result == True

# Test: update_score should log warning and return False if score doesn't exist
def test_update_score_no_existing(redis_service, caplog):
    with patch.object(RedisTrustScoreModel, 'exists', return_value=0):
        with caplog.at_level('WARNING'):
            result = redis_service.update_score('user_1', 99)
            assert result is False
            assert "Attempted to update score for user" in caplog.text

# Test: get_or_load_score should return cached score if it exists
def test_get_or_load_score_existing(redis_service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=b'15'):
        result = redis_service.get_or_load_score('user_1', lambda x: 100)
        assert result == 15

# Test: get_or_load_score should call loader and set value if cache is empty
def test_get_or_load_score_load_and_set(redis_service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=None), \
        patch.object(RedisTrustScoreModel, 'set', return_value=True) as mock_set:
        loader = lambda user_id: 200
        result = redis_service.get_or_load_score('user_1', loader)
        mock_set.assert_called_once_with('user_1', '200', 3600)
        assert result == 200

# Test: get_or_load_score should return 0 if neither cache nor loader returns value
def test_get_or_load_score_load_none(redis_service):
    with patch.object(RedisTrustScoreModel, 'get', return_value=None):
        loader = lambda user_id: None
        result = redis_service.get_or_load_score('user_1', loader)
        assert result == 0
